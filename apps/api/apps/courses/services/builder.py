import logging
from typing import Any

from apps.ai.services import AIService
from apps.courses.models import Course, CourseSection
from apps.documents.models import Document
from apps.ingestion.models import DocumentChunk

logger = logging.getLogger(__name__)


class CourseBuilderService:
    """Transforms analyzed document content and RAG extractions into a complete,

    hierarchical course structure:
    Course -> Chapter -> Section -> Lesson.

    Crucial Rule: All generated content is immediately mutable and editable by teachers.
    AI output is never treated as static or immutable.
    """

    def __init__(self, ai_service: AIService | None = None):
        self.ai_service = ai_service or AIService()

    def generate_course_from_document(
        self,
        course: Course,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 10,
    ) -> Course:
        """Executes RAG-driven AI generation and materializes hierarchical CourseSections."""
        logger.info("Building course %s from analyzed document %s", course.id, document.id)

        # 1. Trigger AI Course generation using AIService facade
        ai_generation = self.ai_service.generate_course(
            document=document,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
        )

        result_data = ai_generation.result or {}

        # 2. Update course metadata if appropriate
        generated_title = result_data.get("title")
        if generated_title and (not course.title or course.title.startswith("Nouveau cours")):
            course.title = generated_title

        intro_text = result_data.get("introduction", "")
        if intro_text and not course.description:
            course.description = intro_text[:500]

        course.document = document
        course.save(update_fields=["title", "description", "document"])

        # 3. Analyze document chunk metadata to identify existing chapters/sections
        doc_chunks = (
            DocumentChunk.objects.filter(document=document)
            .order_by("chunk_index")
            .values("content", "metadata")
        )

        identified_chapters: dict[str, list[dict[str, Any]]] = {}
        for c in doc_chunks:
            meta = c.get("metadata") or {}
            chap = meta.get("chapter") or "Chapitre Général"
            sec = meta.get("section") or "Généralités"
            if chap not in identified_chapters:
                identified_chapters[chap] = []
            identified_chapters[chap].append({"section": sec, "content": c.get("content", "")})

        # 4. Construct hierarchical outline: Course -> Chapter -> Section -> Lesson
        sections_data = result_data.get("sections", [])
        if not sections_data:
            # Fallback structure from document or default intro
            sections_data = [
                {
                    "title": "Fondements et Concepts Clés",
                    "content": intro_text or "Introduction détaillée au contenu du cours.",
                },
                {
                    "title": "Applications Pratiques et Méthodologie",
                    "content": "Développement des notions et cas d'usage pratiques.",
                },
            ]

        # Clear existing draft sections if regenerating
        course.sections.all().delete()

        chapter_order = 0

        # Chapter 1: Introduction & Fondements (Level 1)
        chap1 = CourseSection.objects.create(
            course=course,
            parent=None,
            title="Chapitre 1 : Introduction & Fondements",
            order=chapter_order,
            summary=result_data.get("introduction", "Présentation des objectifs et du contexte."),
            estimated_minutes=30,
        )
        chapter_order += 1

        # Section under Chapter 1 (Level 2)
        sec1 = CourseSection.objects.create(
            course=course,
            parent=chap1,
            title="Section 1.1 : Vue d'ensemble du domaine",
            order=0,
            summary="Synthèse conceptuelle et cadre général.",
            estimated_minutes=15,
        )

        # Lessons under Section 1.1 (Level 3)
        lesson_order = 0
        for s_idx, sec in enumerate(sections_data):
            CourseSection.objects.create(
                course=course,
                parent=sec1,
                title=f"Leçon 1.1.{lesson_order + 1} : {sec.get('title', f'Module {s_idx + 1}')}",
                order=lesson_order,
                content=sec.get("content", ""),
                summary=f"Étude approfondie de : {sec.get('title', '')}",
                objectives=[
                    f"Comprendre les éléments clés de {sec.get('title', '')}",
                    "Être capable d'appliquer les concepts dans un contexte pratique",
                ],
                estimated_minutes=15,
            )
            lesson_order += 1

        # Chapter 2: Approfondissement & Pratique (Level 1)
        chap2 = CourseSection.objects.create(
            course=course,
            parent=None,
            title="Chapitre 2 : Approfondissement & Études de cas",
            order=chapter_order,
            summary="Mise en pratique des compétences et analyse des cas d'usage.",
            estimated_minutes=45,
        )
        chapter_order += 1

        sec2 = CourseSection.objects.create(
            course=course,
            parent=chap2,
            title="Section 2.1 : Mise en œuvre et applications",
            order=0,
            summary="Exercices et scénarios d'application directe.",
            estimated_minutes=25,
        )

        CourseSection.objects.create(
            course=course,
            parent=sec2,
            title="Leçon 2.1.1 : Analyse méthodologique et synthèse",
            order=0,
            content=(
                result_data.get(
                    "conclusion",
                    "Synthèse pédagogique et consolidation des connaissances acquises.",
                )
                + "\n\n"
                + result_data.get("sources_summary", "")
            ),
            summary="Bilan des compétences acquises et révision finale.",
            objectives=[
                "Analyser les résultats et identifier les points de vigilance",
                "Évaluer son niveau de maîtrise du cours",
            ],
            estimated_minutes=20,
        )

        logger.info(
            "Course %s populated with %s total hierarchical sections",
            course.id,
            course.sections.count(),
        )
        return course
