import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.audio.models import AudioContent, AudioStatus
from apps.audio.services.audio_service import AudioPipelineService
from apps.audio.services.providers import (
    MockTTSProvider,
    OpenAITTSProvider,
    get_tts_provider,
    list_available_voices,
)
from apps.audio.services.script_generator import PedagogicalScriptGenerator
from apps.courses.models import Course, CourseLevel, CourseSection, CourseStatus
from apps.documents.services.storage import (
    get_storage_service,
    reset_storage_service,
)
from apps.organizations.models import Organization, OrganizationMember, RoleChoices

User = get_user_model()


class TTSProviderArchitectureTests(APITestCase):
    """Unit tests for the abstract multi-provider TTS architecture."""

    def test_mock_tts_provider_synthesizes_valid_audio(self):
        provider = MockTTSProvider()
        result = provider.synthesize(
            text="Bienvenue dans ce cours sur les architectures modernes de réseaux de neurones.",
            voice_id="pierre",
            language="fr",
        )
        self.assertIsNotNone(result.audio_bytes)
        self.assertTrue(len(result.audio_bytes) > 50)
        # Verify valid MP3 header
        self.assertTrue(result.audio_bytes.startswith(b"ID3"))
        self.assertGreater(result.duration, 1.0)
        self.assertEqual(result.voice_id, "pierre")
        self.assertEqual(result.provider, "mock")

    def test_mock_tts_provider_voices_list(self):
        provider = MockTTSProvider()
        all_voices = provider.get_available_voices()
        self.assertGreater(len(all_voices), 4)

        fr_voices = provider.get_available_voices(language="fr")
        self.assertTrue(all(v.language == "fr" for v in fr_voices))
        self.assertTrue(any(v.id == "pierre" for v in fr_voices))
        self.assertTrue(any(v.id == "marie" for v in fr_voices))

    def test_openai_tts_provider_fallback_without_api_key(self):
        provider = OpenAITTSProvider(api_key="")
        result = provider.synthesize(
            text="Testing speech synthesis with missing API key.",
            voice_id="alloy",
        )
        self.assertIsNotNone(result.audio_bytes)
        self.assertTrue(result.audio_bytes.startswith(b"ID3"))
        self.assertGreater(result.duration, 1.0)

    def test_tts_provider_factory(self):
        mock_prov = get_tts_provider("mock")
        self.assertIsInstance(mock_prov, MockTTSProvider)

        openai_prov = get_tts_provider("openai")
        self.assertIsInstance(openai_prov, OpenAITTSProvider)

    def test_list_all_available_voices(self):
        voices = list_available_voices()
        self.assertGreater(len(voices), 6)
        providers_present = {v["provider"] for v in voices}
        self.assertIn("mock", providers_present)
        self.assertIn("openai", providers_present)


class PedagogicalScriptGeneratorTests(APITestCase):
    """Unit tests for converting written markdown lessons into fluid spoken pedagogical scripts."""

    def setUp(self):
        self.user = User.objects.create_user(email="prof@school.org", password="pwd")
        self.org = Organization.objects.create(name="School")
        self.course = Course.objects.create(
            organization=self.org,
            created_by=self.user,
            title="Intelligence Artificielle",
        )
        self.section = CourseSection.objects.create(
            course=self.course,
            title="Les Réseaux Convolutifs",
            order=1,
            content=(
                "# Introduction aux CNN\n\n"
                "Les réseaux de neurones convolutifs [1] sont spécialement conçus pour les images.\n\n"
                "```python\nmodel.add(Conv2D(32, (3, 3)))\n```\n\n"
                "Principales couches :\n"
                "- Couche de convolution\n"
                "- Couche de pooling\n"
                "- Couche dense finale\n"
            ),
            summary="Les CNN extraient des caractéristiques visuelles hiérarchiques.",
            objectives=["Comprendre les convolutions", "Identifier le pooling"],
        )

    def test_script_generation_cleans_markdown_and_structures_speech(self):
        generator = PedagogicalScriptGenerator()
        script = generator.generate_script(self.section)

        # Introduction should be spoken warmly
        self.assertIn(
            "Bonjour et bienvenue dans cette leçon audio intitulée : Les Réseaux Convolutifs",
            script,
        )

        # Objectives should be mentioned
        self.assertIn("Comprendre les convolutions", script)

        # Markdown header # should be stripped
        self.assertNotIn("# Introduction", script)

        # Code block should be replaced with transitional explanation
        self.assertNotIn("model.add", script)
        self.assertIn("extrait de code", script)

        # Citation [1] should be stripped
        self.assertNotIn("[1]", script)

        # Summary should be synthesized
        self.assertIn("En synthèse de ce module", script)
        self.assertIn("caractéristiques visuelles hiérarchiques", script)


class AudioPipelineAndAPITests(APITestCase):
    """Integration tests for AudioContent API endpoints, Celery asynchronous processing, and storage."""

    def setUp(self):
        self.temp_media_dir = tempfile.mkdtemp()
        self.media_override = override_settings(
            MEDIA_ROOT=self.temp_media_dir,
            STORAGE_BACKEND="local",
        )
        self.media_override.enable()
        reset_storage_service()

        # Tenant A (Alice)
        self.user_a = User.objects.create_user(
            email="alice@univ-a.com",
            password="PasswordA123!",
            first_name="Alice",
        )
        self.org_a = Organization.objects.create(name="Université Alpha")
        OrganizationMember.objects.create(
            organization=self.org_a,
            user=self.user_a,
            role=RoleChoices.TEACHER,
        )

        self.course_a = Course.objects.create(
            organization=self.org_a,
            created_by=self.user_a,
            title="Introduction au Deep Learning",
            level=CourseLevel.BEGINNER,
            status=CourseStatus.PUBLISHED,
        )

        self.section_a = CourseSection.objects.create(
            course=self.course_a,
            title="Mécanismes d'Auto-Attention",
            order=1,
            content="L'auto-attention permet de calculer des pondérations dynamiques entre tokens.",
            summary="Retenir la formule de calcul de l'attention produit-scalaire.",
            objectives=["Comprendre les pondérations", "Calculer l'attention"],
        )

        # Tenant B (Bob) - Isolated
        self.user_b = User.objects.create_user(
            email="bob@univ-b.com",
            password="PasswordB123!",
            first_name="Bob",
        )
        self.org_b = Organization.objects.create(name="Université Beta")
        OrganizationMember.objects.create(
            organization=self.org_b,
            user=self.user_b,
            role=RoleChoices.TEACHER,
        )

        # Tokens
        self.token_a = str(RefreshToken.for_user(self.user_a).access_token)
        self.token_b = str(RefreshToken.for_user(self.user_b).access_token)

    def tearDown(self):
        self.media_override.disable()
        reset_storage_service()
        shutil.rmtree(self.temp_media_dir, ignore_errors=True)

    def _auth_a(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_a}")

    def _auth_b(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_b}")

    @patch("apps.audio.views.generate_section_audio_task.delay")
    def test_post_section_audio_dispatches_async_celery_task_immediately(self, mock_delay):
        """Verifies that POST /sections/{id}/audio returns HTTP 202 Accepted and queues Celery task without blocking."""
        self._auth_a()
        url = reverse("v1:sections:section-audio", kwargs={"id": self.section_a.id})

        payload = {
            "voice_provider": "mock",
            "voice_id": "marie",
            "language": "fr",
        }

        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

        data = response.data
        self.assertEqual(str(data["section_id"]), str(self.section_a.id))
        self.assertEqual(data["status"], AudioStatus.PENDING)
        self.assertEqual(data["voice_id"], "marie")
        self.assertEqual(data["voice_provider"], "mock")

        # Celery task must have been queued asynchronously
        mock_delay.assert_called_once()
        called_audio_id = mock_delay.call_args[0][0]
        self.assertEqual(called_audio_id, data["id"])

        # AudioContent record must exist in DB with PENDING status
        audio_content = AudioContent.objects.get(id=data["id"])
        self.assertEqual(audio_content.status, AudioStatus.PENDING)

    def test_audio_pipeline_execution_end_to_end(self):
        """Tests complete pipeline execution: Lesson -> Script -> TTS -> Storage -> AudioContent COMPLETED."""
        audio_content = AudioContent.objects.create(
            course=self.course_a,
            section=self.section_a,
            voice_provider="mock",
            voice_id="pierre",
            language="fr",
            status=AudioStatus.PENDING,
        )

        service = AudioPipelineService()
        completed = service.process_audio_generation(str(audio_content.id))

        self.assertEqual(completed.status, AudioStatus.COMPLETED)
        self.assertGreater(completed.duration, 1.0)
        self.assertTrue(len(completed.script) > 50)
        self.assertTrue(completed.storage_key.startswith("audio/courses/"))
        self.assertTrue(completed.storage_key.endswith(".mp3"))

        # Verify physical file exists in storage
        storage = get_storage_service()
        self.assertTrue(storage.file_exists(completed.storage_key))

        # Check audio_url property
        url = completed.get_audio_url()
        self.assertIsNotNone(url)
        self.assertIn(completed.storage_key, url)

    def test_get_audio_detail_and_streaming_url(self):
        self._auth_a()
        # Create completed audio
        audio = AudioContent.objects.create(
            course=self.course_a,
            section=self.section_a,
            voice_provider="mock",
            voice_id="pierre",
            script="Bonjour et bienvenue dans la leçon d'auto-attention.",
            storage_key="audio/test_preview.mp3",
            duration=42.5,
            status=AudioStatus.COMPLETED,
        )

        url = reverse("v1:audio:audio-detail", kwargs={"id": audio.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertEqual(data["id"], str(audio.id))
        self.assertEqual(data["duration"], 42.5)
        self.assertEqual(data["status"], AudioStatus.COMPLETED)
        self.assertIn("audio_url", data)
        self.assertIsNotNone(data["audio_url"])

    def test_delete_audio_removes_db_record_and_storage_file(self):
        self._auth_a()
        storage = get_storage_service()
        test_key = "audio/to_delete_test.mp3"
        storage.save_file(test_key, b"ID3\x03fake-audio-bytes")
        self.assertTrue(storage.file_exists(test_key))

        audio = AudioContent.objects.create(
            course=self.course_a,
            section=self.section_a,
            voice_provider="mock",
            storage_key=test_key,
            duration=12.0,
            status=AudioStatus.COMPLETED,
        )

        url = reverse("v1:audio:audio-detail", kwargs={"id": audio.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Database record must be deleted
        self.assertFalse(AudioContent.objects.filter(id=audio.id).exists())

        # Storage file must be removed
        self.assertFalse(storage.file_exists(test_key))

    def test_multi_tenant_isolation_on_audio(self):
        """Bob from Tenant B cannot access or delete Alice's audio from Tenant A."""
        audio = AudioContent.objects.create(
            course=self.course_a,
            section=self.section_a,
            voice_provider="mock",
            storage_key="audio/secret_a.mp3",
            duration=30.0,
            status=AudioStatus.COMPLETED,
        )

        # Bob tries to GET Alice's audio
        self._auth_b()
        url = reverse("v1:audio:audio-detail", kwargs={"id": audio.id})
        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, status.HTTP_403_FORBIDDEN)

        # Bob tries to DELETE Alice's audio
        res_del = self.client.delete(url)
        self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

        # Bob tries to request audio generation on Alice's section
        url_sec = reverse("v1:sections:section-audio", kwargs={"id": self.section_a.id})
        res_post = self.client.post(url_sec, {"voice_id": "alloy"}, format="json")
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

    def test_voices_list_endpoint(self):
        self._auth_a()
        url = reverse("v1:audio:voices-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        voices = response.data["voices"]
        self.assertGreater(len(voices), 4)
        for v in voices:
            self.assertIn("id", v)
            self.assertIn("name", v)
            self.assertIn("language", v)
            self.assertIn("gender", v)
            self.assertIn("provider", v)
