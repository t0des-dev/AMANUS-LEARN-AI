"""AI/RAG-grounded slide deck generation from indexed documents."""

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.ai.models import AIGeneration, GenerationType
from apps.ai.services import MockAIProvider, PromptService
from apps.ai.services.generators.slide_generator import SlideDeckGenerator
from apps.courses.models import Course
from apps.documents.models import Document, DocumentStatus
from apps.ingestion.models import DocumentChunk, DocumentPage
from apps.organizations.models import Organization, OrganizationMember, RoleChoices
from apps.slides.services.slide_generator import SlideGenerator


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        email="slides-ai@amanus.test", password="SecurePassword123!"
    )


@pytest.fixture
def organization(db, owner):
    org = Organization.objects.create(name="Slides AI Academy", slug="slides-ai")
    OrganizationMember.objects.create(
        organization=org, user=owner, role=RoleChoices.TEACHER
    )
    return org


@pytest.fixture
def document_with_chunks(db, organization, owner):
    doc = Document.objects.create(
        organization=organization,
        owner=owner,
        title="Introduction au Deep Learning",
        file_name="deep_learning.pdf",
        file_type="pdf",
        file_size=1024,
        storage_key="test/deep_learning.pdf",
        status=DocumentStatus.READY,
    )
    page = DocumentPage.objects.create(
        document=doc,
        page_number=1,
        text="Introduction aux réseaux de neurones et à la rétropropagation.",
    )
    DocumentChunk.objects.create(
        document=doc,
        page=page,
        chunk_index=0,
        content=(
            "Les réseaux de neurones organisent des unités de calcul en couches. "
            "Le mécanisme d'attention pondère la pertinence de chaque token [1]."
        ),
        token_count=30,
        metadata={"chapter": "Chapitre 1"},
        embedding=[0.05] * 128,
    )
    DocumentChunk.objects.create(
        document=doc,
        page=page,
        chunk_index=1,
        content=(
            "La rétropropagation ajuste les poids par descente de gradient "
            "pour minimiser la fonction de perte [2]."
        ),
        token_count=25,
        metadata={"chapter": "Chapitre 1"},
        embedding=[0.08] * 128,
    )
    return doc


@pytest.fixture
def course_with_document(db, organization, document_with_chunks):
    return Course.objects.create(
        organization=organization,
        title="Cours Deep Learning",
        document=document_with_chunks,
    )


@pytest.fixture
def course_without_document(db, organization):
    return Course.objects.create(organization=organization, title="Cours Sans Doc")


class TestSlidesPrompt:
    def test_prompt_exposes_expected_schema(self):
        _, prompt, version = PromptService().get_slides_prompt("Doc", "[1] ctx")
        assert '"slides":' in prompt
        assert "bullet_points" in prompt
        assert "speaker_notes" in prompt
        assert "slide_number" in prompt
        assert "[x]" in prompt
        assert version.startswith("slides-")

    @pytest.mark.parametrize(
        "language,marker",
        [("fr", "diaporama"), ("en", "slide deck"), ("ar", "شريحة")],
    )
    def test_prompt_language_variants(self, language, marker):
        _, prompt, _ = PromptService().get_slides_prompt(
            "Doc", "ctx", language=language
        )
        assert marker in prompt

    def test_slide_count_directive_included(self):
        _, prompt, _ = PromptService().get_slides_prompt(
            "Doc", "ctx", slide_count=9
        )
        assert "9" in prompt


class TestMockSlidesDispatch:
    @pytest.mark.parametrize(
        "language", ["fr", "en", "ar"], ids=["fr", "en", "ar"]
    )
    def test_mock_returns_slides_payload(self, language):
        service = PromptService()
        system_instruction = service._get_system_instruction(language)
        _, prompt, _ = service.get_slides_prompt("Doc", "[1] ctx", language=language)
        response = MockAIProvider().generate(
            prompt=prompt,
            system_instruction=system_instruction,
            response_format="json",
        )
        assert "slides" in response.parsed_json
        first = response.parsed_json["slides"][0]
        assert first["title"]
        assert isinstance(first["bullet_points"], list)
        assert first["speaker_notes"]


class TestSlideDeckGenerator:
    def test_generate_returns_grounded_ai_payload(self, document_with_chunks):
        result, ai_response, prompt_version = SlideDeckGenerator().generate(
            document=document_with_chunks, provider=MockAIProvider()
        )
        assert isinstance(result, dict)
        assert len(result["slides"]) >= 3
        assert prompt_version.startswith("slides-")
        assert ai_response.input_tokens > 0
        # The mock deck cites sources with bracket references
        assert any(
            "[" in bullet
            for slide in result["slides"]
            for bullet in slide["bullet_points"]
        )

    def test_to_blueprints_converts_bullets_to_content(self):
        payload = {
            "slides": [
                {
                    "slide_number": 1,
                    "title": "Titre",
                    "bullet_points": ["Point A", "Point B"],
                    "speaker_notes": "Notes",
                }
            ]
        }
        blueprints = SlideDeckGenerator.to_blueprints(payload, fallback_title="Doc")
        assert len(blueprints) == 1
        assert blueprints[0]["content"] == "• Point A\n• Point B"
        assert blueprints[0]["slide_number"] == 1
        assert blueprints[0]["slide_type"] == "concept"
        assert blueprints[0]["speaker_notes"] == "Notes"
        assert blueprints[0]["image_prompt"]

    def test_to_blueprints_cleans_markdown_and_caps_bullets(self):
        payload = {
            "slides": [
                {
                    "title": "T",
                    "bullet_points": ["**Gras**", "- Item"]
                    + [f"Point {i}" for i in range(10)],
                }
            ]
        }
        blueprints = SlideDeckGenerator.to_blueprints(payload)
        lines = blueprints[0]["content"].split("\n")
        assert len(lines) == 6
        assert lines[0] == "• Gras"
        assert lines[1] == "• Item"

    def test_to_blueprints_skips_empty_slides_and_renumbers(self):
        payload = {
            "slides": [
                {"title": "Vide", "bullet_points": []},
                {"title": "Bon", "bullet_points": ["X"]},
            ]
        }
        blueprints = SlideDeckGenerator.to_blueprints(payload)
        assert len(blueprints) == 1
        assert blueprints[0]["slide_number"] == 1
        assert blueprints[0]["title"] == "Bon"

    def test_to_blueprints_handles_invalid_payload(self):
        assert SlideDeckGenerator.to_blueprints({}) == []
        assert SlideDeckGenerator.to_blueprints({"slides": "nope"}) == []
        assert SlideDeckGenerator.to_blueprints(None) == []


class TestSlideGeneratorAIPath:
    def test_uses_ai_when_document_is_indexed(self, course_with_document):
        presentation = SlideGenerator().generate_presentation(
            course=course_with_document
        )
        assert presentation.status == "READY"
        slides = list(presentation.slides.order_by("slide_number"))
        assert len(slides) >= 3
        assert all(slide.content for slide in slides)
        assert any("•" in slide.content for slide in slides)

        audit = AIGeneration.objects.get(
            document=course_with_document.document, type=GenerationType.SLIDES
        )
        assert audit.status == "SUCCESS"
        assert "slides" in audit.result

    def test_records_requesting_user_on_audit(self, course_with_document, owner):
        SlideGenerator().generate_presentation(
            course=course_with_document, user=owner
        )
        audit = AIGeneration.objects.get(type=GenerationType.SLIDES)
        assert audit.user == owner

    def test_falls_back_to_heuristic_without_document(self, course_without_document):
        presentation = SlideGenerator().generate_presentation(
            course=course_without_document
        )
        assert presentation.status == "READY"
        assert presentation.slides.count() >= 4
        assert not AIGeneration.objects.filter(type=GenerationType.SLIDES).exists()

    def test_falls_back_to_heuristic_on_ai_failure(self, course_with_document):
        class BrokenService:
            def generate_slides(self, **kwargs):
                raise RuntimeError("provider down")

        presentation = SlideGenerator(
            generation_service=BrokenService()
        ).generate_presentation(course=course_with_document)
        assert presentation.status == "READY"
        assert presentation.slides.count() >= 4
        assert not AIGeneration.objects.filter(type=GenerationType.SLIDES).exists()

    def test_ai_failure_leaves_no_presentation_marked_failed(
        self, course_with_document
    ):
        class BrokenService:
            def generate_slides(self, **kwargs):
                raise RuntimeError("provider down")

        presentation = SlideGenerator(
            generation_service=BrokenService()
        ).generate_presentation(course=course_with_document)
        assert presentation.status != "FAILED"


class TestSlidesGenerationAPI:
    @pytest.mark.django_db
    def test_endpoint_generates_ai_grounded_deck(
        self, course_with_document, owner
    ):
        token = RefreshToken.for_user(owner)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
        response = client.post(
            f"/api/v1/courses/{course_with_document.id}/presentations/",
            {"title": "Deck IA", "theme": "modern_dark"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["status"] == "READY"
        assert len(response.data["slides"]) >= 3
        assert AIGeneration.objects.filter(
            document=course_with_document.document, type=GenerationType.SLIDES
        ).exists()
