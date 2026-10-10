import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.audio.models import AudioContent, AudioStatus
from apps.audio.services.audio_assembler import AudioAssembler
from apps.audio.services.audio_service import AudioPipelineService
from apps.audio.services.providers.base import (
    TTSAudioResult,
    TTSProviderError,
)
from apps.audio.services.providers.openai_provider import OpenAITTSProvider
from apps.audio.services.script_generator import PedagogicalScriptGenerator
from apps.audio.services.text_processor import AudioTextSegmenter
from apps.courses.models import Course, CourseLevel, CourseSection, CourseStatus
from apps.organizations.models import Organization, OrganizationMember, RoleChoices

User = get_user_model()


@pytest.fixture
def org_and_users(db):
    org_a = Organization.objects.create(name="Université des Sciences", slug="univ-sciences-s3")
    user_a = User.objects.create_user(
        email="prof.alain@sciences.edu",
        password="TestPassword123!",
        first_name="Alain",
        last_name="Turing",
    )
    OrganizationMember.objects.create(organization=org_a, user=user_a, role=RoleChoices.TEACHER)

    # Isolated tenant B
    org_b = Organization.objects.create(name="Académie Littéraire", slug="acad-lettres-s3")
    user_b = User.objects.create_user(
        email="prof.beatrice@lettres.edu",
        password="TestPassword123!",
        first_name="Béatrice",
        last_name="Beauvoir",
    )
    OrganizationMember.objects.create(organization=org_b, user=user_b, role=RoleChoices.TEACHER)

    return (org_a, user_a), (org_b, user_b)


@pytest.fixture
def course_and_section(db, org_and_users):
    (org_a, user_a), _ = org_and_users
    course = Course.objects.create(
        organization=org_a,
        created_by=user_a,
        title="Traitement Automatique du Langage Naturel",
        language="fr",
        level=CourseLevel.INTERMEDIATE,
        status=CourseStatus.PUBLISHED,
    )
    section = CourseSection.objects.create(
        course=course,
        title="Modèles de Langage et Tokenisation",
        order=1,
        content=(
            "La tokenisation décompose le texte en sous-mots. "
            "Les modèles comme BERT et GPT utilisent Byte-Pair Encoding (BPE)."
        ),
        summary="Retenir les principes de découpage BPE et WordPiece.",
        objectives=["Comprendre BPE", "Analyser les tokens"],
    )
    return course, section


@pytest.mark.django_db
class TestAudioTextSegmenterAndPreparation:
    """Tests text segmentation, sentence boundaries, and multilingual script generator."""

    def test_segment_text_short_returns_single_chunk(self):
        text = "Une phrase d'introduction courte pour tester la synthèse vocale."
        chunks = AudioTextSegmenter.segment_text(text, max_chunk_chars=500)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_segment_text_empty_or_whitespace_returns_empty_list(self):
        assert AudioTextSegmenter.segment_text("") == []
        assert AudioTextSegmenter.segment_text("   \n\t   ") == []

    def test_segment_text_long_preserves_all_words_without_loss_or_duplication(self):
        # Generate text with 20 sentences and ~6000 characters
        sentences = [
            f"Ceci est la phrase explicative numéro {i} sur les architectures neuronales et l'attention."
            for i in range(1, 60)
        ]
        full_text = " ".join(sentences)
        assert len(full_text) > 4000

        chunks = AudioTextSegmenter.segment_text(full_text, max_chunk_chars=1200)
        assert len(chunks) >= 4

        # Verify all chunks are below limit
        for c in chunks:
            assert len(c) <= 1200
            assert not c.startswith(" ")
            assert not c.endswith(" ")

        # Reconstructed content must contain all sentences
        reconstructed = " ".join(chunks)
        for s in sentences:
            assert s in reconstructed

    def test_arabic_script_generation_and_unicode_preservation(self, org_and_users):
        (org_a, user_a), _ = org_and_users
        course_ar = Course.objects.create(
            organization=org_a,
            created_by=user_a,
            title="الذكاء الاصطناعي ومعالجة اللغات",
            language="ar",
        )
        sec_ar = CourseSection.objects.create(
            course=course_ar,
            title="المفاهيم الجوهرية لشبكات العصبونية",
            order=1,
            content="تعتمد الشبكات العصبونية على ترابط العقد ومعالجة الإشارات الرقمية.",
            summary="فهم الخوارزميات الحسابية وطرق التدريب الميداني.",
            objectives=["فهم بنية العقد", "حساب أوزان الترابط"],
        )

        gen = PedagogicalScriptGenerator()
        script = gen.generate_script(sec_ar, language="ar")

        assert "أهلاً ومرحباً بكم في هذا الدرس الصوتي بعنوان" in script
        assert "المفاهيم الجوهرية لشبكات العصبونية" in script
        assert "في خلاصة هذا المحور" in script
        assert "بهذا نختتم تسجيلنا الصوتي" in script


@pytest.mark.django_db
class TestAudioAssemblerAndValidation:
    """Tests audio byte validation, ID3 header stripping, and multi-segment assembly."""

    def test_validate_audio_bytes_success(self):
        valid_mock_mp3 = b"ID3\x03\x00\x00\x00\x00\x00\x00" + (b"\xff\xfb\x90\x64" * 20)
        assert AudioAssembler.validate_audio_bytes(valid_mock_mp3) is True

    def test_validate_audio_bytes_rejects_empty_or_tiny_stream(self):
        with pytest.raises(TTSProviderError):
            AudioAssembler.validate_audio_bytes(b"")

        with pytest.raises(TTSProviderError):
            AudioAssembler.validate_audio_bytes(b"RIFFtiny")

    def test_validate_audio_bytes_rejects_invalid_magic_signature(self):
        corrupt_bytes = b"CORRUPTED_NON_AUDIO_PAYLOAD_" * 10
        with pytest.raises(TTSProviderError, match="Format audio invalide"):
            AudioAssembler.validate_audio_bytes(corrupt_bytes)

    def test_strip_id3_header_removes_tag_cleanly(self):
        # 10 byte header with size 0 synchsafe: 10 bytes total
        id3_tag = b"ID3\x03\x00\x00\x00\x00\x00\x00"
        payload = b"\xff\xfb\x90\x64" * 10
        full = id3_tag + payload

        stripped = AudioAssembler.strip_id3_header(full)
        assert stripped == payload
        assert not stripped.startswith(b"ID3")

    def test_assemble_segments_combines_durations_and_removes_middle_id3(self):
        seg1 = TTSAudioResult(
            audio_bytes=b"ID3\x03\x00\x00\x00\x00\x00\x00" + (b"\xff\xfb\x90\x64" * 20),
            duration=3.5,
            format="mp3",
            voice_id="pierre",
            provider="mock",
        )
        seg2 = TTSAudioResult(
            audio_bytes=b"ID3\x03\x00\x00\x00\x00\x00\x00" + (b"\xff\xfb\x90\x64" * 25),
            duration=5.0,
            format="mp3",
            voice_id="pierre",
            provider="mock",
        )

        assembled = AudioAssembler.assemble_segments([seg1, seg2])
        assert assembled.duration == 8.5
        assert assembled.audio_bytes.startswith(b"ID3")
        # Middle ID3 should be stripped: only one 'ID3' at index 0
        assert assembled.audio_bytes.count(b"ID3") == 1
        assert len(assembled.audio_bytes) > len(seg1.audio_bytes)


@pytest.mark.django_db
class TestTTSProvidersAndErrorHandling:
    """Tests provider error recovery, retries, and API key presence."""

    def test_openai_provider_raises_tts_error_on_http_failure(self):
        provider = OpenAITTSProvider(api_key="sk-mock-testing-key")

        # Mock urllib.request.urlopen raising HTTPError 401
        with patch("urllib.request.urlopen") as mock_url:
            mock_url.side_effect = urllib.error.HTTPError(
                url="https://api.openai.com/v1/audio/speech",
                code=401,
                msg="Unauthorized",
                hdrs={},
                fp=None,
            )
            with pytest.raises(TTSProviderError, match="401"):
                provider.synthesize("Test phrase.")

    def test_openai_provider_retries_on_transient_error(self):
        provider = OpenAITTSProvider(api_key="sk-mock-testing-key")

        # First call raises 429, second call succeeds with valid MP3 bytes
        mock_resp = MagicMock()
        mock_resp.read.return_value = b"ID3\x03\x00\x00\x00\x00\x00\x00" + (
            b"\xff\xfb\x90\x64" * 20
        )
        mock_resp.__enter__.return_value = mock_resp

        err_429 = urllib.error.HTTPError(
            url="https://api.openai.com/v1/audio/speech",
            code=429,
            msg="Rate limit",
            hdrs={},
            fp=None,
        )

        with patch("urllib.request.urlopen", side_effect=[err_429, mock_resp]):
            res = provider.synthesize("Test phrase after rate limit.")
            assert res.audio_bytes.startswith(b"ID3")
            assert res.provider == "openai"


@pytest.mark.django_db
class TestAudioPipelineAndConcurrency:
    """Tests end-to-end audio pipeline, storage, multi-chunk, and 409 conflict."""

    def test_pipeline_rejects_empty_script(self, course_and_section):
        course, section = course_and_section
        audio_content = AudioContent.objects.create(
            course=course,
            section=section,
            script="   \n   ",
            status=AudioStatus.PENDING,
        )

        # Clear section content to ensure generated script is also empty
        section.content = ""
        section.summary = ""
        section.title = ""
        section.save()

        service = AudioPipelineService()
        # When script is blank, pipeline raises ValueError
        audio_content.script = " "
        audio_content.save()

        with patch.object(service.script_generator, "generate_script", return_value="   "):
            with pytest.raises(ValueError, match="vide"):
                service.process_audio_generation(str(audio_content.id))

        audio_content.refresh_from_db()
        assert audio_content.status == AudioStatus.FAILED

    def test_pipeline_multi_chunk_segmentation_end_to_end(self, course_and_section):
        course, section = course_and_section
        long_script = " ".join([f"Explication détaillée étape {i}." for i in range(1, 150)])
        assert len(long_script) > 3000

        audio_content = AudioContent.objects.create(
            course=course,
            section=section,
            voice_provider="mock",
            voice_id="pierre",
            language="fr",
            script=long_script,
            status=AudioStatus.PENDING,
        )

        service = AudioPipelineService()
        completed = service.process_audio_generation(str(audio_content.id))

        assert completed.status == AudioStatus.COMPLETED
        assert completed.duration > 10.0
        assert completed.storage_key.startswith("audio/courses/")
        assert completed.get_audio_url() is not None

    def test_concurrent_processing_audio_returns_409_conflict(
        self, org_and_users, course_and_section
    ):
        (org_a, user_a), _ = org_and_users
        course, section = course_and_section

        # Create audio in PROCESSING status
        AudioContent.objects.create(
            course=course,
            section=section,
            voice_provider="mock",
            voice_id="marie",
            status=AudioStatus.PROCESSING,
        )

        client = APIClient()
        client.force_authenticate(user=user_a)

        url = f"/api/v1/sections/{section.id}/audio"
        response = client.post(
            url,
            {"voice_provider": "mock", "voice_id": "marie"},
            format="json",
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["code"] == "audio_generation_in_progress"

    def test_cross_tenant_isolation_forbidden(self, org_and_users, course_and_section):
        _, (org_b, user_b) = org_and_users
        course, section = course_and_section

        audio = AudioContent.objects.create(
            course=course,
            section=section,
            voice_provider="mock",
            voice_id="pierre",
            status=AudioStatus.COMPLETED,
            storage_key="audio/courses/c1/sections/s1.mp3",
        )

        # User B from Org B tries to access Org A's audio
        client = APIClient()
        client.force_authenticate(user=user_b)

        # Direct detail view
        res = client.get(f"/api/v1/audio/{audio.id}")
        assert res.status_code == status.HTTP_403_FORBIDDEN

        # Section audio endpoint
        res_sec = client.get(f"/api/v1/sections/{section.id}/audio")
        assert res_sec.status_code == status.HTTP_403_FORBIDDEN
