import uuid
from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status

from apps.ai.services.providers.base import AIResponse
from apps.ai.services.providers.mock_provider import MockAIProvider
from apps.courses.models import Course, CourseLevel, CourseSection
from apps.courses.services.builder import CourseBuilderService
from apps.courses.services.validator import CoursePayloadValidator, InvalidCoursePayloadError
from apps.courses.tasks import generate_course_task


@pytest.mark.django_db
class TestCoursePayloadValidator:
    """Test suite for CoursePayloadValidator (Contract validation, normalization, edge cases)."""

    def test_validate_valid_payload_french(self):
        validator = CoursePayloadValidator(default_language="fr")
        raw = {
            "title": "Introduction à l'IA",
            "description": "Cours complet",
            "level": "BEGINNER",
            "learning_objectives": ["Comprendre les réseaux de neurones"],
            "chapters": [
                {
                    "title": "### Chapitre 1 : Les Fondements",
                    "summary": "Concepts de base",
                    "estimated_minutes": 45,
                    "sections": [
                        {
                            "title": "**Leçon 1.1** : Le Perceptron",
                            "content": "Description du perceptron simple [1].",
                            "summary": "Résumé du perceptron",
                            "objectives": ["Identifier une fonction d'activation"],
                            "estimated_minutes": 20,
                        }
                    ],
                }
            ],
            "conclusion": "Bilan du cours",
        }

        normalized = validator.validate(raw)
        assert normalized["title"] == "Introduction à l'IA"
        assert normalized["level"] == "BEGINNER"
        assert len(normalized["chapters"]) == 1

        chap = normalized["chapters"][0]
        # Verify markdown heading cleanup
        assert chap["title"] == "Chapitre 1 : Les Fondements"
        assert chap["estimated_minutes"] == 45
        assert len(chap["sections"]) == 1

        sec = chap["sections"][0]
        assert sec["title"] == "Leçon 1.1 : Le Perceptron"
        assert sec["content"] == "Description du perceptron simple [1]."
        assert sec["estimated_minutes"] == 20

    def test_validate_valid_payload_arabic(self):
        validator = CoursePayloadValidator(default_language="ar")
        raw = {
            "title": "مقرر الذكاء الاصطناعي",
            "description": "مقرر شامل باللغة العربية",
            "level": "INTERMEDIATE",
            "learning_objectives": ["استيعاب خوارزميات التعلم الآلي"],
            "chapters": [
                {
                    "title": "الفصل 1 : الشبكات العصبية",
                    "summary": "ملخص شامل",
                    "sections": [
                        {
                            "title": "الدرس 1.1 : التعلم العميق",
                            "content": "شرح مفصل للشبكات العميقة وتطبيقاتها [1].",
                            "summary": "خلاصة الدرس",
                            "objectives": ["فهم آلية التغذية الأمامية"],
                        }
                    ],
                }
            ],
        }

        normalized = validator.validate(raw)
        assert normalized["title"] == "مقرر الذكاء الاصطناعي"
        assert normalized["level"] == "INTERMEDIATE"
        assert len(normalized["chapters"]) == 1
        assert "الشبكات العصبية" in normalized["chapters"][0]["title"]
        assert "التعلم العميق" in normalized["chapters"][0]["sections"][0]["title"]

    def test_validate_rejects_empty_or_non_dict_payload(self):
        validator = CoursePayloadValidator()
        with pytest.raises(InvalidCoursePayloadError, match="doit être un dictionnaire JSON"):
            validator.validate([])

        with pytest.raises(InvalidCoursePayloadError, match="vide"):
            validator.validate({})

    def test_validate_handles_flat_sections_by_creating_chapter(self):
        validator = CoursePayloadValidator(default_language="en")
        raw = {
            "title": "Flat Course Structure",
            "sections": [
                {
                    "title": "Section 1 : Getting Started",
                    "content": "Step by step installation [1].",
                },
                {
                    "title": "Section 2 : Next Steps",
                    "content": "Advanced usage guide [2].",
                },
            ],
        }

        normalized = validator.validate(raw)
        assert len(normalized["chapters"]) >= 1
        all_section_titles = [s["title"] for ch in normalized["chapters"] for s in ch["sections"]]
        assert "Section 1 : Getting Started" in all_section_titles
        assert "Section 2 : Next Steps" in all_section_titles

    def test_validate_deduplicates_identical_chapters(self):
        validator = CoursePayloadValidator()
        raw = {
            "title": "Duplicated Course",
            "chapters": [
                {
                    "title": "Chapitre 1 : Introduction",
                    "sections": [{"title": "Leçon 1", "content": "Contenu A"}],
                },
                {
                    "title": "Chapitre 1 : Introduction",  # Duplicate title
                    "sections": [{"title": "Leçon 1", "content": "Contenu B"}],
                },
                {
                    "title": "Chapitre 2 : Approfondissement",
                    "sections": [{"title": "Leçon 2", "content": "Contenu C"}],
                },
            ],
        }

        normalized = validator.validate(raw)
        # Should have deduplicated to 2 chapters
        assert len(normalized["chapters"]) == 2
        assert normalized["chapters"][0]["title"] == "Chapitre 1 : Introduction"
        assert normalized["chapters"][1]["title"] == "Chapitre 2 : Approfondissement"

    def test_validate_rejects_empty_structure(self):
        validator = CoursePayloadValidator()
        raw = {
            "title": "Empty Structure",
            "chapters": [],
            "sections": [],
        }
        with pytest.raises(
            InvalidCoursePayloadError, match="ne contient aucun chapitre ni section"
        ):
            validator.validate(raw)


@pytest.mark.django_db
class TestCourseBuilderServiceSprint01:
    """Test suite for CourseBuilderService improvements (multilingual, level, preserve_existing, atomic)."""

    def test_builder_populates_arabic_course(self, tenant_setup, analyzed_document):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="مقرر جديد",
            document=analyzed_document,
            language="ar",
            level=CourseLevel.BEGINNER,
        )

        builder = CourseBuilderService(provider=MockAIProvider())
        updated_course = builder.generate_from_document(
            course=course,
            document=analyzed_document,
            user=teacher,
            language="ar",
            level="BEGINNER",
        )

        assert updated_course.title is not None
        assert updated_course.language == "ar"
        assert updated_course.sections.count() >= 3

        chapters = updated_course.sections.filter(parent__isnull=True)
        assert chapters.count() >= 2
        for chap in chapters:
            assert chap.course == updated_course
            # Verify child lessons exist
            assert chap.children.count() >= 1

    def test_builder_preserves_teacher_edited_sections_when_requested(
        self, tenant_setup, analyzed_document
    ):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Cours Mixte",
            document=analyzed_document,
        )

        # Teacher pre-creates an editorial section
        manual_section = CourseSection.objects.create(
            course=course,
            title="Chapitre Manuel du Professeur",
            order=1,
            summary="Rédigé à la main avant l'IA",
            content="Contenu expert unique à conserver absolument.",
        )

        builder = CourseBuilderService(provider=MockAIProvider())
        # Call generate with preserve_existing=True
        builder.generate_from_document(
            course=course,
            document=analyzed_document,
            user=teacher,
            preserve_existing=True,
        )

        # The manually created section must still exist!
        assert CourseSection.objects.filter(id=manual_section.id).exists()
        reloaded_manual = CourseSection.objects.get(id=manual_section.id)
        assert reloaded_manual.title == "Chapitre Manuel du Professeur"
        assert reloaded_manual.content == "Contenu expert unique à conserver absolument."

        # And additional generated sections should have been created
        total_sections = course.sections.count()
        assert total_sections > 1

    def test_builder_replaces_sections_when_preserve_existing_false(
        self, tenant_setup, analyzed_document
    ):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Cours Remplaçable",
            document=analyzed_document,
        )

        # Teacher pre-creates an old draft section
        old_section = CourseSection.objects.create(
            course=course,
            title="Ancien brouillon à écraser",
            order=1,
        )

        builder = CourseBuilderService(provider=MockAIProvider())
        builder.generate_from_document(
            course=course,
            document=analyzed_document,
            user=teacher,
            preserve_existing=False,
        )

        # The old section should have been replaced
        assert not CourseSection.objects.filter(id=old_section.id).exists()
        assert course.sections.count() >= 3

    def test_builder_handles_ai_provider_empty_content(self, tenant_setup, analyzed_document):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Cours Erreur Test",
            document=analyzed_document,
        )

        # Mock provider returning empty content
        mock_provider = MagicMock()
        mock_provider.name = "failing_mock"
        mock_provider.default_model = "test-model"
        mock_provider.generate.return_value = AIResponse(
            content="",
            parsed_json=None,
            input_tokens=10,
            output_tokens=0,
            model="test-model",
            provider="failing_mock",
        )

        builder = CourseBuilderService(provider=mock_provider)
        with pytest.raises(InvalidCoursePayloadError):
            builder.generate_from_document(
                course=course,
                document=analyzed_document,
                user=teacher,
            )

    def test_builder_handles_ai_provider_exception_without_corrupting_db(
        self, tenant_setup, analyzed_document
    ):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Cours Transaction Test",
            document=analyzed_document,
        )
        CourseSection.objects.create(
            course=course,
            title="Section Initiale",
            order=1,
        )

        mock_provider = MagicMock()
        mock_provider.name = "error_mock"
        mock_provider.default_model = "test-model"
        mock_provider.generate.side_effect = RuntimeError("Service LLM indisponible")

        builder = CourseBuilderService(provider=mock_provider)
        with pytest.raises(RuntimeError, match="Service LLM indisponible"):
            builder.generate_from_document(
                course=course,
                document=analyzed_document,
                user=teacher,
                preserve_existing=False,
            )

        # Atomic transaction rollback: Section Initiale must still exist
        assert course.sections.count() == 1
        assert course.sections.first().title == "Section Initiale"


@pytest.mark.django_db
class TestCeleryAsyncCourseGeneration:
    """Test suite for asynchronous course generation Celery task."""

    def test_generate_course_task_success(self, tenant_setup, analyzed_document):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Cours Asynchrone",
            document=analyzed_document,
        )

        result = generate_course_task(
            course_id=str(course.id),
            user_id=str(teacher.id),
            document_id=str(analyzed_document.id),
            provider_name="mock",
            language="fr",
            level="INTERMEDIATE",
            preserve_existing=False,
        )

        assert result["status"] == "SUCCESS"
        assert result["course_id"] == str(course.id)
        assert result["sections_count"] >= 3

        course.refresh_from_db()
        assert course.level == CourseLevel.INTERMEDIATE
        assert course.sections.count() >= 3

    def test_generate_course_task_handles_missing_course(self, tenant_setup):
        teacher = tenant_setup["teacher"]
        fake_course_id = str(uuid.uuid4())

        result = generate_course_task(
            course_id=fake_course_id,
            user_id=str(teacher.id),
        )

        assert result["status"] == "ERROR"
        assert "introuvable" in result["error"]


@pytest.mark.django_db
class TestCourseGenerationAPIEndpointSprint01:
    """Test suite for API endpoint options (language, level, async_mode, preserve_existing)."""

    def test_api_generate_with_arabic_and_advanced_level(
        self, api_client, tenant_setup, analyzed_document
    ):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Cours Arabe Avancé",
            document=analyzed_document,
        )

        api_client.force_authenticate(user=teacher)
        url = f"/api/v1/courses/{course.id}/generate/"
        response = api_client.post(
            url,
            {
                "provider": "mock",
                "language": "ar",
                "level": "ADVANCED",
                "focus": "Focaliser sur l'optimisation",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["id"] == str(course.id)
        assert len(data["sections"]) > 0

        course.refresh_from_db()
        assert course.language == "ar"
        assert course.level == CourseLevel.ADVANCED

    def test_api_generate_with_async_mode(self, api_client, tenant_setup, analyzed_document):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Cours Mode Async",
            document=analyzed_document,
        )

        api_client.force_authenticate(user=teacher)
        url = f"/api/v1/courses/{course.id}/generate/"

        with patch("apps.courses.tasks.generate_course_task.delay") as mock_delay:
            mock_delay.return_value = MagicMock(id="task-uuid-123")
            response = api_client.post(
                url,
                {
                    "provider": "mock",
                    "async_mode": True,
                },
                format="json",
            )

            assert response.status_code == status.HTTP_202_ACCEPTED
            assert response.data["status"] == "PENDING"
            assert response.data["task_id"] == "task-uuid-123"
            mock_delay.assert_called_once()

    def test_api_rejects_invalid_language(self, api_client, tenant_setup, analyzed_document):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Test Validation Lang",
            document=analyzed_document,
        )

        api_client.force_authenticate(user=teacher)
        url = f"/api/v1/courses/{course.id}/generate/"
        response = api_client.post(
            url,
            {"language": "invalid_lang"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "language" in response.data

    def test_api_rejects_invalid_level(self, api_client, tenant_setup, analyzed_document):
        teacher = tenant_setup["teacher"]
        org = tenant_setup["org_a"]

        course = Course.objects.create(
            organization=org,
            created_by=teacher,
            title="Test Validation Level",
            document=analyzed_document,
        )

        api_client.force_authenticate(user=teacher)
        url = f"/api/v1/courses/{course.id}/generate/"
        response = api_client.post(
            url,
            {"level": "UNKNOWN_LEVEL"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "level" in response.data
