import logging
from typing import Any

from django.db import transaction

from apps.ai.services import AIService
from apps.courses.models import Course, CourseLevel, CourseSection
from apps.courses.services.validator import CoursePayloadValidator
from apps.documents.models import Document
from apps.ingestion.models import DocumentChunk

logger = logging.getLogger(__name__)


class CourseBuilderService:
    """Transforms analyzed document content and RAG extractions into a complete,
    hierarchical course structure:
    Course -> Chapter -> Section / Lesson.

    Crucial Rules:
    1. All generated content is immediately mutable and editable by teachers.
    2. Strict validation and normalization ensures resilient, pedagogical output.
    3. Structural chapters from document metadata and multilingual headings (FR, AR, EN)
       are respected.
    4. Database changes are wrapped in atomic transactions to prevent partial or destructive state.
    """

    def __init__(
        self,
        ai_service: AIService | None = None,
        validator: CoursePayloadValidator | None = None,
        provider: Any | None = None,
    ):
        if provider is not None:
            self.ai_service = AIService(provider=provider)
        else:
            self.ai_service = ai_service or AIService()
        self.validator = validator or CoursePayloadValidator()

    def generate_from_document(self, *args: Any, **kwargs: Any) -> Course:
        """Convenience alias for generate_course_from_document."""
        return self.generate_course_from_document(*args, **kwargs)

    def generate_course_from_document(
        self,
        course: Course,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 10,
        language: str | None = None,
        level: str | None = None,
        preserve_existing: bool = False,
    ) -> Course:
        """Executes RAG-driven AI generation and materializes hierarchical CourseSections."""
        logger.info(
            "Building course %s from analyzed document %s (lang=%s, level=%s, preserve=%s)",
            course.id,
            document.id,
            language,
            level,
            preserve_existing,
        )

        target_lang = (
            language
            or getattr(course, "language", None)
            or getattr(document, "detected_language", None)
            or getattr(document, "language", None)
            or "fr"
        )
        target_level = level or getattr(course, "level", None) or CourseLevel.BEGINNER

        # 1. Trigger AI Course generation using AIService facade
        ai_generation = self.ai_service.generate_course(
            document=document,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
            language=target_lang,
            level=target_level,
        )

        result_data = ai_generation.result or {}

        # 2. Extract document chunk metadata to identify existing chapters/sections
        doc_chunks = (
            DocumentChunk.objects.filter(document=document)
            .order_by("chunk_index")
            .values("content", "metadata")
        )

        identified_chapters: dict[str, list[dict[str, Any]]] = {}
        for c in doc_chunks:
            meta = c.get("metadata") or {}
            chap = meta.get("chapter")
            sec = meta.get("section") or "Généralités"
            if chap:
                if chap not in identified_chapters:
                    identified_chapters[chap] = []
                identified_chapters[chap].append({"section": sec, "content": c.get("content", "")})

        # 3. Validate and normalize the course blueprint
        validated_blueprint = self.validator.validate_and_normalize(
            raw_data=result_data,
            language=target_lang,
            default_level=target_level,
            identified_chapters=identified_chapters if len(identified_chapters) > 1 else None,
        )

        # 4. Atomic database persistence
        with transaction.atomic():
            # Update Course metadata
            gen_title = validated_blueprint.get("title")
            if gen_title and (
                not course.title
                or course.title.startswith("Nouveau cours")
                or course.title.startswith("New course")
                or course.title.startswith("دورة جديدة")
            ):
                course.title = gen_title

            gen_desc = validated_blueprint.get("description")
            if gen_desc and not course.description:
                course.description = gen_desc[:500]

            course.level = validated_blueprint.get("level", target_level)
            course.language = target_lang
            course.document = document
            course.save(update_fields=["title", "description", "level", "language", "document"])

            # Manage existing sections
            if not preserve_existing:
                course.sections.all().delete()
                chapter_order = 0
            else:
                chapter_order = course.sections.filter(parent__isnull=True).count()

            # 5. Materialize hierarchical Chapters -> Lessons
            chapters_data = validated_blueprint.get("chapters", [])
            for ch_idx, ch_data in enumerate(chapters_data):
                chap_obj = CourseSection.objects.create(
                    course=course,
                    parent=None,
                    title=ch_data["title"],
                    order=chapter_order,
                    summary=ch_data.get("summary", ""),
                    estimated_minutes=ch_data.get("estimated_minutes", 30),
                )
                chapter_order += 1

                lessons_data = ch_data.get("sections", [])
                for l_idx, l_data in enumerate(lessons_data):
                    CourseSection.objects.create(
                        course=course,
                        parent=chap_obj,
                        title=l_data["title"],
                        order=l_idx,
                        content=l_data.get("content", ""),
                        summary=l_data.get("summary", ""),
                        objectives=l_data.get("objectives", []),
                        estimated_minutes=l_data.get("estimated_minutes", 15),
                    )

        logger.info(
            "Course %s successfully populated with %s total hierarchical sections",
            course.id,
            course.sections.count(),
        )
        return course
