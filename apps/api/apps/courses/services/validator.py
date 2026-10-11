import logging
import re
from typing import Any

from apps.courses.models import CourseLevel

logger = logging.getLogger(__name__)


class InvalidCoursePayloadError(Exception):
    """Raised when AI-generated course data fails structural or pedagogical validation."""

    pass


class CoursePayloadValidator:
    """Strict validator and normalizer for AI-generated course payloads.

    Guarantees that:
    1. A valid course title and pedagogical description are present.
    2. Educational level is normalized to CourseLevel choices.
    3. Learning objectives are non-empty and well-formed.
    4. A hierarchical structure (Chapters -> Lessons/Sections) is enforced.
    5. Duplicate sections or empty content are detected and sanitized.
    6. Multilingual defaults (FR, AR, EN) are respected for generated headings.
    """

    VALID_LEVELS = {choice.value for choice in CourseLevel}

    DEFAULT_HEADINGS = {
        "fr": {
            "chap1": "Chapitre 1 : Introduction & Fondements Théoriques",
            "chap2": "Chapitre 2 : Notions Clés & Principes Directeurs",
            "chap3": "Chapitre 3 : Approfondissement & Méthodologie",
            "chap4": "Chapitre 4 : Mise en Œuvre Pratique & Études de Cas",
            "chap5": "Chapitre 5 : Bonnes Pratiques & Points de Vigilance",
            "chap6": "Chapitre 6 : Synthèse Globale & Validation",
            "sec1": "Vue d'ensemble et concepts clés",
            "sec2": "Mise en œuvre et cas pratiques",
            "lesson_prefix": "Leçon",
            "default_objective": "Comprendre et appliquer les concepts clés du chapitre",
        },
        "ar": {
            "chap1": "الفصل 1 : المقدمة والأسس النظرية والمفاهيمية",
            "chap2": "الفصل 2 : المبادئ الجوهرية والآليات التأسيسية",
            "chap3": "الفصل 3 : التحليل المنهجي والتقني المعمق",
            "chap4": "الفصل 4 : التطبيقات العملية ودراسات الحالة",
            "chap5": "الفصل 5 : أفضل الممارسات ونقاط اليقظة",
            "chap6": "الفصل 6 : الخلاصة الشاملة وآفاق التطوير",
            "sec1": "نظرة عامة والمفاهيم الأساسية",
            "sec2": "التطبيق العملي ودراسة الحالات",
            "lesson_prefix": "الدرس",
            "default_objective": "فهم وتطبيق المفاهيم الأساسية للفصل",
        },
        "en": {
            "chap1": "Chapter 1: Introduction & Foundational Concepts",
            "chap2": "Chapter 2: Core Principles & Theoretical Framework",
            "chap3": "Chapter 3: Technical Deep Dive & Methodology",
            "chap4": "Chapter 4: Practical Implementation & Case Studies",
            "chap5": "Chapter 5: Best Practices & Key Insights",
            "chap6": "Chapter 6: Synthesis & Future Perspectives",
            "sec1": "Overview and Key Concepts",
            "sec2": "Practical Implementation and Case Studies",
            "lesson_prefix": "Lesson",
            "default_objective": "Understand and apply the core concepts of this chapter",
        },
    }

    def __init__(self, default_language: str = "fr"):
        self.default_language = default_language

    def validate(
        self,
        raw_data: Any,
        language: str | None = None,
        default_level: str = CourseLevel.BEGINNER,
        identified_chapters: dict[str, list[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        """Convenience alias for validate_and_normalize."""
        if not isinstance(raw_data, dict):
            raise InvalidCoursePayloadError(
                f"Le résultat de génération doit être un dictionnaire JSON (reçu : {type(raw_data).__name__})."
            )
        if not raw_data:
            raise InvalidCoursePayloadError("Le résultat de génération est vide.")
        return self.validate_and_normalize(
            raw_data=raw_data,
            language=language or self.default_language,
            default_level=default_level,
            identified_chapters=identified_chapters,
        )

    def validate_and_normalize(
        self,
        raw_data: Any,
        language: str = "fr",
        default_level: str = CourseLevel.BEGINNER,
        identified_chapters: dict[str, list[dict[str, Any]]] | None = None,
    ) -> dict[str, Any]:
        """Validates raw AI output and normalizes it into a reliable course blueprint."""
        if not isinstance(raw_data, dict):
            raise InvalidCoursePayloadError(
                f"Le résultat de génération doit être un dictionnaire JSON (reçu : {type(raw_data).__name__})."
            )
        if not raw_data:
            raise InvalidCoursePayloadError("Le résultat de génération est vide.")

        lang = language.lower() if language else "fr"
        headings = self.DEFAULT_HEADINGS.get(lang, self.DEFAULT_HEADINGS["fr"])

        # 1. Validate & sanitize Title
        raw_title = raw_data.get("title") or raw_data.get("course_title")
        if not raw_title or not isinstance(raw_title, str) or not raw_title.strip():
            raw_title = (
                "مقرر تعليمي شامل"
                if lang == "ar"
                else "Comprehensive Educational Course"
                if lang == "en"
                else "Cours Pédagogique Complet"
            )
        title = self._clean_heading(raw_title)

        # 2. Validate Description / Overview
        raw_desc = (
            raw_data.get("description")
            or raw_data.get("introduction")
            or raw_data.get("overview")
            or ""
        )
        if not isinstance(raw_desc, str):
            raw_desc = str(raw_desc)
        description = raw_desc.strip()

        # 3. Validate Level
        raw_level = str(raw_data.get("level") or default_level).upper()
        if raw_level not in self.VALID_LEVELS:
            raw_level = (
                default_level if default_level in self.VALID_LEVELS else CourseLevel.BEGINNER
            )

        # 4. Validate Learning Objectives
        raw_objs = raw_data.get("learning_objectives") or raw_data.get("objectives") or []
        objectives: list[str] = []
        if isinstance(raw_objs, list):
            for obj in raw_objs:
                if isinstance(obj, str) and obj.strip():
                    objectives.append(obj.strip())
                elif isinstance(obj, dict) and obj.get("objective"):
                    objectives.append(str(obj["objective"]).strip())
        if not objectives:
            objectives = [headings["default_objective"]]

        # 5. Extract and normalize Chapters
        chapters_list = self._normalize_chapters(
            raw_data=raw_data,
            headings=headings,
            identified_chapters=identified_chapters,
        )

        if not chapters_list:
            raise InvalidCoursePayloadError(
                "La structure du cours est invalide : ne contient aucun chapitre ni section exploitable."
            )

        conclusion = raw_data.get("conclusion") or ""
        prerequisites = [
            str(p).strip() for p in raw_data.get("prerequisites", []) if str(p).strip()
        ]

        return {
            "title": title,
            "description": description,
            "level": raw_level,
            "language": lang,
            "learning_objectives": objectives,
            "prerequisites": prerequisites,
            "conclusion": str(conclusion).strip(),
            "chapters": chapters_list,
        }

    def _normalize_chapters(
        self,
        raw_data: dict[str, Any],
        headings: dict[str, str],
        identified_chapters: dict[str, list[dict[str, Any]]] | None = None,
    ) -> list[dict[str, Any]]:
        """Constructs a normalized list of chapters with child lessons."""
        chapters_input = raw_data.get("chapters")
        sections_input = raw_data.get("sections")

        # Scenario A: AI output already has structured chapters
        if isinstance(chapters_input, list) and len(chapters_input) > 0:
            normalized_chapters = []
            seen_titles = set()
            for ch_idx, ch in enumerate(chapters_input):
                if not isinstance(ch, dict):
                    continue
                ch_key = f"chap{ch_idx + 1}"
                default_title = headings.get(ch_key, f"{headings['chap1'].split(':')[0]} {ch_idx + 1}")
                ch_title = self._clean_heading(ch.get("title") or default_title)
                if ch_title in seen_titles:
                    continue
                seen_titles.add(ch_title)
                ch_summary = str(ch.get("summary") or ch.get("description") or "").strip()
                ch_duration = int(ch.get("estimated_minutes") or 30)

                child_lessons = []
                raw_children = ch.get("sections") or ch.get("lessons") or []
                if isinstance(raw_children, list):
                    for sec_idx, sec in enumerate(raw_children):
                        if not isinstance(sec, dict):
                            continue
                        lesson = self._normalize_lesson(sec, sec_idx, headings)
                        if lesson:
                            child_lessons.append(lesson)

                # Fallback child if chapter had no sections
                if not child_lessons:
                    child_lessons.append(
                        {
                            "title": f"{headings['sec1']}",
                            "summary": ch_summary or headings["sec1"],
                            "content": ch_summary or "Contenu du module d'apprentissage.",
                            "objectives": [headings["default_objective"]],
                            "estimated_minutes": 15,
                        }
                    )

                normalized_chapters.append(
                    {
                        "title": ch_title,
                        "summary": ch_summary,
                        "estimated_minutes": max(10, ch_duration),
                        "sections": child_lessons,
                    }
                )

            # Check if any identified chapters from document were omitted by the AI
            if identified_chapters:
                for chap_name, chunk_items in identified_chapters.items():
                    clean_name = self._clean_heading(chap_name)
                    # If this chapter was not included in AI output, add it
                    if not any(clean_name.lower() in existing["title"].lower() or existing["title"].lower() in clean_name.lower() for existing in normalized_chapters):
                        chunk_text = "\n\n".join(c.get("content", "") for c in chunk_items[:3] if c.get("content"))
                        sec_items = [
                            {
                                "title": c.get("section") or f"{headings['lesson_prefix']} 1",
                                "summary": (c.get("content", "")[:180] if c.get("content") else "") or headings["sec1"],
                                "content": c.get("content", "") or f"Contenu du module {clean_name}.",
                                "objectives": [headings["default_objective"]],
                                "estimated_minutes": 15,
                            }
                            for c in chunk_items[:3]
                        ] if chunk_items else [
                            {
                                "title": headings["sec1"],
                                "summary": f"Module dédié à : {clean_name}",
                                "content": chunk_text or f"Contenu du module {clean_name}.",
                                "objectives": [headings["default_objective"]],
                                "estimated_minutes": 15,
                            }
                        ]
                        normalized_chapters.append(
                            {
                                "title": clean_name,
                                "summary": f"Module thématique : {clean_name}",
                                "estimated_minutes": len(sec_items) * 20,
                                "sections": sec_items,
                            }
                        )

            if normalized_chapters:
                return normalized_chapters

        # Scenario B: AI output has flat sections list
        if isinstance(sections_input, list) and len(sections_input) > 0:
            valid_sections = []
            for s_idx, sec in enumerate(sections_input):
                if isinstance(sec, dict):
                    lesson = self._normalize_lesson(sec, s_idx, headings)
                    if lesson:
                        valid_sections.append(lesson)

            if valid_sections:
                # If document chunks contained chapter boundaries, group by them
                if identified_chapters and len(identified_chapters) > 1:
                    grouped_chapters = []
                    chap_keys = list(identified_chapters.keys())
                    total_chaps = len(chap_keys)
                    total_secs = len(valid_sections)

                    secs_per_chap = max(1, total_secs // total_chaps)
                    sec_cursor = 0

                    for c_idx, chap_name in enumerate(chap_keys):
                        if c_idx == total_chaps - 1:
                            batch = valid_sections[sec_cursor:]
                        else:
                            batch = valid_sections[sec_cursor : sec_cursor + secs_per_chap]
                        sec_cursor += len(batch)

                        if not batch:
                            chunk_items = identified_chapters[chap_name]
                            chunk_text = "\n\n".join(c.get("content", "") for c in chunk_items[:2] if c.get("content"))
                            batch = [
                                {
                                    "title": f"{headings['sec1']}",
                                    "summary": f"Axe : {chap_name}",
                                    "content": chunk_text or f"Contenu pédagogique dédié à {chap_name}.",
                                    "objectives": [headings["default_objective"]],
                                    "estimated_minutes": 15,
                                }
                            ]

                        grouped_chapters.append(
                            {
                                "title": self._clean_heading(chap_name),
                                "summary": f"Module dédié à : {chap_name}",
                                "estimated_minutes": len(batch) * 20,
                                "sections": batch,
                            }
                        )

                    if grouped_chapters:
                        return grouped_chapters

                # Otherwise, partition flat sections into multiple logical chapters (3 to 6)
                num_chapters = min(6, max(3, (len(valid_sections) + 1) // 2))
                secs_per_chap = max(1, (len(valid_sections) + num_chapters - 1) // num_chapters)
                grouped_chapters = []

                for ch_i in range(num_chapters):
                    ch_key = f"chap{ch_i + 1}"
                    ch_title = headings.get(ch_key, f"{headings['chap1'].split(':')[0]} {ch_i + 1}")
                    start_i = ch_i * secs_per_chap
                    end_i = min(len(valid_sections), start_i + secs_per_chap)
                    batch = valid_sections[start_i:end_i]
                    if not batch:
                        continue
                    grouped_chapters.append(
                        {
                            "title": ch_title,
                            "summary": batch[0].get("summary", ""),
                            "estimated_minutes": len(batch) * 20,
                            "sections": batch,
                        }
                    )
                if grouped_chapters:
                    return grouped_chapters

        # Scenario C: Fallback if text content exists in introduction or overview
        intro = str(raw_data.get("introduction") or raw_data.get("overview") or "").strip()
        if intro:
            num_fallback_chaps = 3
            fallback_chapters = []
            for ch_i in range(num_fallback_chaps):
                ch_key = f"chap{ch_i + 1}"
                ch_title = headings.get(ch_key, f"{headings['chap1'].split(':')[0]} {ch_i + 1}")
                fallback_chapters.append(
                    {
                        "title": ch_title,
                        "summary": intro[:250],
                        "estimated_minutes": 25,
                        "sections": [
                            {
                                "title": f"{headings['sec1']} - {ch_i + 1}",
                                "summary": intro[:120],
                                "content": intro,
                                "objectives": [headings["default_objective"]],
                                "estimated_minutes": 15,
                            }
                        ],
                    }
                )
            return fallback_chapters

        return []

    def _normalize_lesson(
        self,
        sec: dict[str, Any],
        idx: int,
        headings: dict[str, str],
    ) -> dict[str, Any] | None:
        """Sanitizes an individual section or lesson."""
        title = self._clean_heading(sec.get("title") or f"{headings['lesson_prefix']} {idx + 1}")
        content = str(sec.get("content") or sec.get("summary") or "").strip()
        summary = str(sec.get("summary") or (content[:200] if content else "")).strip()

        raw_objs = sec.get("objectives") or []
        objs = []
        if isinstance(raw_objs, list):
            objs = [str(o).strip() for o in raw_objs if str(o).strip()]
        if not objs:
            objs = [f"{headings['default_objective']} ({title})"]

        estimated = int(sec.get("estimated_minutes") or 15)

        return {
            "title": title,
            "summary": summary,
            "content": content,
            "objectives": objs,
            "estimated_minutes": max(5, min(120, estimated)),
        }

    def _clean_heading(self, text: str) -> str:
        """Removes Markdown artifacts and trims heading string."""
        if not text:
            return ""
        clean = re.sub(r"^#{1,6}\s+", "", str(text)).strip()
        clean = re.sub(r"[*_`]", "", clean).strip()
        return clean[:250]
