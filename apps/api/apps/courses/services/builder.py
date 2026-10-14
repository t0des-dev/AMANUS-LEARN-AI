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
        effective_top_k = max(top_k, 25)
        ai_generation = self.ai_service.generate_course(
            document=document,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=effective_top_k,
            language=target_lang,
            level=target_level,
        )

        result_data = ai_generation.result or {}

        # 2. Extract document chunk metadata to identify existing chapters/sections
        doc_chunks = list(
            DocumentChunk.objects.filter(document=document)
            .order_by("chunk_index")
            .values("content", "metadata")
        )

        from apps.ingestion.parsers.structure_detector import detect_structure

        identified_chapters: dict[str, list[dict[str, Any]]] = {}
        for c in doc_chunks:
            meta = c.get("metadata") or {}
            chap = meta.get("chapter")
            sec = meta.get("section") or "Généralités"
            if not chap:
                detected = detect_structure(c.get("content", ""))
                chap = detected.get("chapter")
                if detected.get("section"):
                    sec = detected["section"]
            if chap:
                if chap not in identified_chapters:
                    identified_chapters[chap] = []
                identified_chapters[chap].append({"section": sec, "content": c.get("content", "")})

        # If document has multiple chunks but fewer than 2 distinct chapters detected,
        # partition chunks into 4 to 6 logical thematic modules covering the whole document
        if len(doc_chunks) >= 3 and len(identified_chapters) <= 1:
            total_chunks = len(doc_chunks)
            num_modules = min(6, max(3, (total_chunks + 2) // 3))
            chunks_per_mod = max(1, (total_chunks + num_modules - 1) // num_modules)

            thematic_titles = {
                "fr": [
                    "Chapitre 1 : Introduction & Fondements Théoriques",
                    "Chapitre 2 : Notions Clés & Principes Directeurs",
                    "Chapitre 3 : Approfondissement Technique & Méthodologie",
                    "Chapitre 4 : Mise en Œuvre Pratique & Cas d'Usage",
                    "Chapitre 5 : Bonnes Pratiques & Points de Vigilance",
                    "Chapitre 6 : Synthèse Globale & Perspectives",
                ],
                "ar": [
                    "الفصل 1 : المقدمة والأسس النظرية والمفاهيمية",
                    "الفصل 2 : المبادئ الجوهرية والآليات التأسيسية",
                    "الفصل 3 : التحليل المنهجي والتقني المعمق",
                    "الفصل 4 : التطبيقات العملية ودراسات الحالة",
                    "الفصل 5 : أفضل الممارسات ونقاط اليقظة",
                    "الفصل 6 : الخلاصة الشاملة وآفاق التطوير",
                ],
                "en": [
                    "Chapter 1: Introduction & Foundational Concepts",
                    "Chapter 2: Core Principles & Theoretical Framework",
                    "Chapter 3: Technical Deep Dive & Methodology",
                    "Chapter 4: Practical Implementation & Case Studies",
                    "Chapter 5: Best Practices & Key Insights",
                    "Chapter 6: Synthesis & Future Perspectives",
                ],
            }
            lang_titles = thematic_titles.get(target_lang, thematic_titles["fr"])
            identified_chapters = {}
            for m_idx in range(num_modules):
                m_title = lang_titles[m_idx] if m_idx < len(lang_titles) else f"Chapitre {m_idx + 1}"
                start_c = m_idx * chunks_per_mod
                end_c = min(total_chunks, start_c + chunks_per_mod)
                mod_chunks = doc_chunks[start_c:end_c]
                if mod_chunks:
                    identified_chapters[m_title] = [
                        {"section": f"Section {m_idx + 1}.{s_i + 1}", "content": c.get("content", "")}
                        for s_i, c in enumerate(mod_chunks)
                    ]

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

            # 5. Materialize hierarchical Chapters (Axes) -> Lessons with full document content
            chapters_data = validated_blueprint.get("chapters", [])
            total_doc_chunks = len(doc_chunks)
            total_blueprint_lessons = max(1, sum(len(ch.get("sections", [])) for ch in chapters_data))
            chunks_per_lesson = max(1, (total_doc_chunks + total_blueprint_lessons - 1) // total_blueprint_lessons)

            global_lesson_counter = 0

            for ch_idx, ch_data in enumerate(chapters_data):
                ch_title = ch_data["title"]
                ch_summary = ch_data.get("summary", "")

                # Provide rich introductory content for the Axis / Chapter
                if target_lang == "ar":
                    default_desc = "استعراض شامل ومفصل لكافة المفاهيم والموضوعات المندرجة ضمن هذا المحور."
                    chap_content = (
                        f"# {ch_title}\n\n"
                        f"## نظرة عامة على المحور وأهدافه\n\n"
                        f"{ch_summary or default_desc}\n\n"
                        f"> **توجيه منهجي :** استيعاب تسلسل الدروس التفاعلية التابعة لهذا المحور وفق الترتيب البيداغوجي المعتمد."
                    )
                elif target_lang == "en":
                    default_desc = "Comprehensive overview of foundational concepts covered under this learning axis."
                    chap_content = (
                        f"# {ch_title}\n\n"
                        f"## Axis Overview and Objectives\n\n"
                        f"{ch_summary or default_desc}\n\n"
                        f"> **Pedagogical Note:** Review the interactive lessons sequentially to consolidate understanding."
                    )
                else:
                    default_desc = "Vue d'ensemble détaillée des concepts et principes abordés dans cet axe."
                    chap_content = (
                        f"# {ch_title}\n\n"
                        f"## Présentation de l'Axe et Objectifs\n\n"
                        f"{ch_summary or default_desc}\n\n"
                        f"> **Note méthodologique :** Suivre les leçons interactives de ce module selon la progression pédagogique."
                    )

                chap_obj = CourseSection.objects.create(
                    course=course,
                    parent=None,
                    title=ch_title,
                    order=chapter_order,
                    summary=ch_summary,
                    content=chap_content,
                    estimated_minutes=ch_data.get("estimated_minutes", 30),
                )
                chapter_order += 1

                lessons_data = ch_data.get("sections", [])
                for l_idx, l_data in enumerate(lessons_data):
                    l_title = l_data["title"]
                    existing_content = (l_data.get("content") or "").strip()
                    existing_summary = (l_data.get("summary") or "").strip()

                    # Assign corresponding document chunks to this lesson (with cyclic fallback)
                    if total_doc_chunks > 0:
                        c_start = (global_lesson_counter * chunks_per_lesson) % total_doc_chunks
                        c_end = min(total_doc_chunks, c_start + max(1, chunks_per_lesson))
                        lesson_chunks = doc_chunks[c_start:c_end]
                        if not lesson_chunks:
                            lesson_chunks = [doc_chunks[global_lesson_counter % total_doc_chunks]]
                    else:
                        lesson_chunks = []
                    global_lesson_counter += 1

                    # Check if existing content is insufficient (too brief, template placeholder, or lacks narrative depth)
                    is_too_brief = len(existing_content) < 650 or existing_content.count("\n") < 3
                    is_generic = (
                        "Contenu du module" in existing_content
                        or "شرح تفصيلي وغني" in existing_content
                        or "Développement pédagogique" in existing_content
                    )

                    if (is_too_brief or is_generic) and lesson_chunks:
                        chunk_bodies = [c.get("content", "").strip() for c in lesson_chunks if c.get("content", "").strip()]
                        extracted_text = "\n\n".join(chunk_bodies)

                        if extracted_text:
                            if target_lang == "ar":
                                if existing_content and not is_generic:
                                    final_content = (
                                        f"{existing_content}\n\n"
                                        f"### الشرح المعمق والتحليل الموثق من نصوص الوثيقة\n\n"
                                        f"{extracted_text}\n\n"
                                        f"> **ملاحظة تأطيرية :** تم تأصيل وبناء محتوى هذا الدرس مباشرة من نصوص الوثيقة المعتمدة [1]."
                                    )
                                else:
                                    final_content = (
                                        f"## {l_title}\n\n"
                                        f"### المضمون التعليمي والشرح المعمق\n\n"
                                        f"{extracted_text}\n\n"
                                        f"### النقاط الرئيسية المستخلصة\n"
                                        f"- استخلاص وتحليل المفاهيم الجوهرية الموثقة في المستند [1].\n"
                                        f"- التطبيق العملي والمعايير المنهجية المتبعة [2].\n\n"
                                        f"> **ملاحظة تأطيرية :** يرتكز هذا الدرس بصورة كاملة ومباشرة على نصوص الوثيقة المستخرجة."
                                    )
                            elif target_lang == "en":
                                if existing_content and not is_generic:
                                    final_content = (
                                        f"{existing_content}\n\n"
                                        f"### Detailed Explanations & Source Grounding\n\n"
                                        f"{extracted_text}\n\n"
                                        f"> **Important Note:** This lesson strictly reflects the complete extracted document content [1]."
                                    )
                                else:
                                    final_content = (
                                        f"## {l_title}\n\n"
                                        f"### Core Educational Content & Analysis\n\n"
                                        f"{extracted_text}\n\n"
                                        f"### Key Learning Takeaways\n"
                                        f"- Core conceptual insights directly extracted from source material [1].\n"
                                        f"- Methodological principles and real-world guidelines [2].\n\n"
                                        f"> **Important Note:** This lesson strictly reflects the complete extracted document content."
                                    )
                            else:
                                if existing_content and not is_generic:
                                    final_content = (
                                        f"{existing_content}\n\n"
                                        f"### Développement Didactique & Contenu Approfondi\n\n"
                                        f"{extracted_text}\n\n"
                                        f"> **Règle fondamentale :** Le contenu de cette leçon est intégralement extrait et structuré à partir du document [1]."
                                    )
                                else:
                                    final_content = (
                                        f"## {l_title}\n\n"
                                        f"### Contenu Pédagogique Détaillé\n\n"
                                        f"{extracted_text}\n\n"
                                        f"### Points Clés & Synthèse Didactique\n"
                                        f"- Analyse approfondie des notions directement issues du document source [1].\n"
                                        f"- Mise en pratique méthodologique et directives opérationnelles [2].\n\n"
                                        f"> **Règle fondamentale :** Le contenu de cette leçon est intégralement extrait et structuré à partir du document."
                                    )
                        else:
                            final_content = existing_content
                    else:
                        final_content = existing_content

                    sec_obj = CourseSection.objects.create(
                        course=course,
                        parent=chap_obj,
                        title=l_title,
                        order=l_idx,
                        content=final_content,
                        summary=existing_summary or (final_content[:200] + "..."),
                        objectives=l_data.get("objectives", []),
                        estimated_minutes=l_data.get("estimated_minutes", 15),
                    )

                    # Also persist sub-lessons if present in data
                    sub_lessons = l_data.get("sections") or l_data.get("lessons") or []
                    if isinstance(sub_lessons, list) and sub_lessons:
                        for sub_idx, sub_data in enumerate(sub_lessons):
                            if isinstance(sub_data, dict):
                                CourseSection.objects.create(
                                    course=course,
                                    parent=sec_obj,
                                    title=sub_data.get("title", f"Leçon {l_idx + 1}.{sub_idx + 1}"),
                                    order=sub_idx,
                                    content=sub_data.get("content", ""),
                                    summary=sub_data.get("summary", ""),
                                    objectives=sub_data.get("objectives", []),
                                    estimated_minutes=sub_data.get("estimated_minutes", 15),
                                )

        logger.info(
            "Course %s successfully populated with %s total hierarchical sections",
            course.id,
            course.sections.count(),
        )
        return course
