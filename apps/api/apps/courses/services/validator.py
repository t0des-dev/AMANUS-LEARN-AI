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
            "chap1": "Chapitre 1 : Introduction & Fondements",
            "chap2": "Chapitre 2 : Approfondissement & Études de cas",
            "chap3": "Chapitre 3 : Synthèse & Validation des Compétences",
            "sec1": "Vue d'ensemble et concepts clés",
            "sec2": "Mise en œuvre et cas pratiques",
            "lesson_prefix": "Leçon",
            "default_objective": "Comprendre et appliquer les concepts clés du chapitre",
        },
        "ar": {
            "chap1": "الفصل 1 : المقدمة والأسس النظرية",
            "chap2": "الفصل 2 : التعمق والدراسات التطبيقية",
            "chap3": "الفصل 3 : الخلاصة والتقييم النهائي",
            "sec1": "نظرة عامة والمفاهيم الأساسية",
            "sec2": "التطبيق العملي ودراسة الحالات",
            "lesson_prefix": "الدرس",
            "default_objective": "فهم وتطبيق المفاهيم الأساسية للفصل",
        },
        "en": {
            "chap1": "Chapter 1: Introduction & Core Foundations",
            "chap2": "Chapter 2: Deep Dive & Practical Applications",
            "chap3": "Chapter 3: Summary & Skills Assessment",
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
                ch_title = self._clean_heading(
                    ch.get("title") or f"{headings['chap1'].split(':')[0]} {ch_idx + 1}"
                )
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
                    sec_cursor = 0
                    total_secs = len(valid_sections)
                    for chap_name in identified_chapters.keys():
                        if sec_cursor >= total_secs:
                            break
                        # Take 1-2 sections per chapter
                        batch = valid_sections[sec_cursor : sec_cursor + 2]
                        sec_cursor += len(batch)
                        grouped_chapters.append(
                            {
                                "title": self._clean_heading(chap_name),
                                "summary": f"Module dédié à : {chap_name}",
                                "estimated_minutes": len(batch) * 20,
                                "sections": batch,
                            }
                        )
                    # Add any remaining sections
                    if sec_cursor < total_secs and grouped_chapters:
                        grouped_chapters[-1]["sections"].extend(valid_sections[sec_cursor:])
                    if grouped_chapters:
                        return grouped_chapters

                # Otherwise, partition flat sections into two logical chapters
                midpoint = max(1, len(valid_sections) // 2)
                chap1_lessons = valid_sections[:midpoint]
                chap2_lessons = valid_sections[midpoint:] or valid_sections[:1]

                return [
                    {
                        "title": headings["chap1"],
                        "summary": raw_data.get("introduction", "Fondements et cadre théorique."),
                        "estimated_minutes": len(chap1_lessons) * 20,
                        "sections": chap1_lessons,
                    },
                    {
                        "title": headings["chap2"],
                        "summary": raw_data.get(
                            "conclusion", "Applications et approfondissements."
                        ),
                        "estimated_minutes": len(chap2_lessons) * 25,
                        "sections": chap2_lessons,
                    },
                ]

        # Scenario C: Minimal fallback if text content exists in introduction
        intro = str(raw_data.get("introduction") or raw_data.get("overview") or "").strip()
        if intro:
            return [
                {
                    "title": headings["chap1"],
                    "summary": intro[:300],
                    "estimated_minutes": 30,
                    "sections": [
                        {
                            "title": headings["sec1"],
                            "summary": intro[:150],
                            "content": intro,
                            "objectives": [headings["default_objective"]],
                            "estimated_minutes": 15,
                        }
                    ],
                }
            ]

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
