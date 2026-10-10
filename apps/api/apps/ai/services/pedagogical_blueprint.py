"""Pedagogical Blueprint Service & Schema for Amanus Learn AI (Sprint 10).

Provides a unified, versioned (blueprint-v1.0), and validated pedagogical representation
acting as the single source of truth across all educational formats:
- Courses and lessons
- Multi-tier summaries (very_short, synthetic, detailed)
- Grounded quizzes with objective mapping
- Spoken audio narratives
- Slide presentations and visual decks
"""

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from apps.courses.models import Course, CourseLevel

logger = logging.getLogger(__name__)

BLUEPRINT_SCHEMA_VERSION = "blueprint-v1.0"


class InvalidPedagogicalBlueprintError(Exception):
    """Raised when a pedagogical blueprint fails structural or pedagogical validation."""

    pass


@dataclass
class LearningObjective:
    id: str
    taxonomy_level: str  # e.g., 'Comprendre', 'Appliquer', 'Analyser', 'Évaluer'
    description: str
    source_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KeyConcept:
    term: str
    canonical_definition: str
    importance: str = "CORE"  # 'CORE' or 'SECONDARY'
    source_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SectionOutline:
    order: int
    title: str
    key_explanation: str
    source_facts: list[str] = field(default_factory=list)
    pedagogical_examples: list[str] = field(default_factory=list)
    summary: str = ""
    estimated_minutes: int = 15

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PedagogicalBlueprint:
    """Canonical pedagogical blueprint linking source document to all derived formats."""

    title: str
    subject: str
    target_audience: str
    level: str  # CourseLevel: BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    prerequisites: list[str] = field(default_factory=list)
    learning_objectives: list[dict[str, Any]] = field(default_factory=list)
    key_concepts: list[dict[str, Any]] = field(default_factory=list)
    sections_outline: list[dict[str, Any]] = field(default_factory=list)
    key_takeaways: list[str] = field(default_factory=list)
    source_references: list[dict[str, Any]] = field(default_factory=list)
    self_assessment_checks: list[str] = field(default_factory=list)
    version: str = BLUEPRINT_SCHEMA_VERSION
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def sections(self) -> list[dict[str, Any]]:
        """Alias for sections_outline to facilitate generic consumer access."""
        return self.sections_outline


class PedagogicalBlueprintValidator:
    """Strict validator for PedagogicalBlueprint payloads."""

    VALID_LEVELS = {choice.value for choice in CourseLevel}

    @classmethod
    def validate_and_build(cls, raw: dict[str, Any], default_level: str = CourseLevel.BEGINNER) -> PedagogicalBlueprint:
        """Validates raw payload and constructs a PedagogicalBlueprint instance."""
        data = cls.validate_and_normalize(raw, default_level=default_level)
        return PedagogicalBlueprint(**data)

    @classmethod
    def validate_and_normalize(cls, raw: dict[str, Any], default_level: str = CourseLevel.BEGINNER) -> dict[str, Any]:
        """Validates raw blueprint dictionary and returns normalized, safe structure."""
        if not isinstance(raw, dict):
            raise InvalidPedagogicalBlueprintError(
                f"Le schéma de base pédagogique doit être un dictionnaire JSON (reçu : {type(raw).__name__})."
            )

        title = str(raw.get("title", "")).strip()
        if not title:
            raise InvalidPedagogicalBlueprintError("Titre du blueprint manquant ou vide.")

        subject = str(raw.get("subject", "")).strip() or title
        target_audience = str(raw.get("target_audience", "")).strip() or "Apprenants en formation"

        # Normalize educational level
        raw_level = str(raw.get("level", "")).strip().upper()
        level = raw_level if raw_level in cls.VALID_LEVELS else default_level

        # Prerequisites
        raw_prereqs = raw.get("prerequisites", [])
        prerequisites = [str(p).strip() for p in raw_prereqs if str(p).strip()] if isinstance(raw_prereqs, list) else []

        # Learning objectives
        raw_objectives = raw.get("learning_objectives", [])
        normalized_objectives: list[dict[str, Any]] = []
        if isinstance(raw_objectives, list):
            for idx, obj in enumerate(raw_objectives, start=1):
                if isinstance(obj, dict):
                    desc = str(obj.get("description", obj.get("objective", ""))).strip()
                    tax = str(obj.get("taxonomy_level", obj.get("level", "Comprendre"))).strip()
                    s_ref = str(obj.get("source_ref", "")).strip()
                elif isinstance(obj, str) and obj.strip():
                    desc = obj.strip()
                    tax = "Comprendre"
                    s_ref = ""
                else:
                    continue

                if desc:
                    normalized_objectives.append({
                        "id": f"obj_{idx}",
                        "taxonomy_level": tax,
                        "description": desc,
                        "source_ref": s_ref,
                    })

        if not normalized_objectives:
            normalized_objectives.append({
                "id": "obj_1",
                "taxonomy_level": "Comprendre",
                "description": f"Comprendre les notions fondamentales de {title}",
                "source_ref": "[1]",
            })

        # Key concepts
        raw_concepts = raw.get("key_concepts", [])
        normalized_concepts: list[dict[str, Any]] = []
        if isinstance(raw_concepts, list):
            for c in raw_concepts:
                if isinstance(c, dict):
                    term = str(c.get("term", c.get("concept", ""))).strip()
                    defn = str(c.get("canonical_definition", c.get("definition", ""))).strip()
                    imp = str(c.get("importance", "CORE")).strip().upper()
                    s_ref = str(c.get("source_ref", "")).strip()
                elif isinstance(c, str) and c.strip():
                    term = c.strip()
                    defn = f"Notion clé relative à {term}"
                    imp = "CORE"
                    s_ref = ""
                else:
                    continue

                if term and defn:
                    normalized_concepts.append({
                        "term": term,
                        "canonical_definition": defn,
                        "importance": imp if imp in ("CORE", "SECONDARY") else "CORE",
                        "source_ref": s_ref,
                    })

        # Sections outline
        raw_sections = raw.get("sections_outline", raw.get("chapters", []))
        normalized_sections: list[dict[str, Any]] = []
        if isinstance(raw_sections, list):
            for idx, s in enumerate(raw_sections, start=1):
                if isinstance(s, dict):
                    s_title = str(s.get("title", f"Section {idx}")).strip()
                    key_expl = str(s.get("key_explanation", s.get("content", s.get("summary", "")))).strip()
                    s_facts = [str(f).strip() for f in s.get("source_facts", []) if str(f).strip()]
                    p_examples = [str(e).strip() for e in s.get("pedagogical_examples", []) if str(e).strip()]
                    summary = str(s.get("summary", "")).strip()
                    mins = int(s.get("estimated_minutes", 15)) if str(s.get("estimated_minutes", "")).isdigit() else 15
                else:
                    continue

                normalized_sections.append({
                    "order": idx,
                    "title": s_title,
                    "key_explanation": key_expl,
                    "source_facts": s_facts,
                    "pedagogical_examples": p_examples,
                    "summary": summary,
                    "estimated_minutes": max(5, min(mins, 180)),
                })

        # Key takeaways
        raw_takeaways = raw.get("key_takeaways", [])
        key_takeaways = [str(t).strip() for t in raw_takeaways if str(t).strip()] if isinstance(raw_takeaways, list) else []

        # Source references
        raw_sources = raw.get("source_references", raw.get("citations", []))
        source_references: list[dict[str, Any]] = []
        if isinstance(raw_sources, list):
            for src in raw_sources:
                if isinstance(src, dict):
                    source_references.append(src)

        # Self assessment checks
        raw_checks = raw.get("self_assessment_checks", [])
        self_assessment_checks = [str(c).strip() for c in raw_checks if str(c).strip()] if isinstance(raw_checks, list) else []

        return {
            "title": title,
            "subject": subject,
            "target_audience": target_audience,
            "level": level,
            "prerequisites": prerequisites,
            "learning_objectives": normalized_objectives,
            "key_concepts": normalized_concepts,
            "sections_outline": normalized_sections,
            "key_takeaways": key_takeaways,
            "source_references": source_references,
            "self_assessment_checks": self_assessment_checks,
            "version": BLUEPRINT_SCHEMA_VERSION,
            "metadata": raw.get("metadata", {}),
        }


class PedagogicalBlueprintService:
    """Manages the lifecycle, extraction, derivation, and persistence of pedagogical blueprints."""

    def __init__(self, validator: PedagogicalBlueprintValidator | None = None):
        self.validator = validator or PedagogicalBlueprintValidator()

    def derive_from_course(self, course: Course) -> PedagogicalBlueprint:
        """Derives a normalized PedagogicalBlueprint from an existing Course and its hierarchical sections.

        Enables derived formats (Quizzes, Summaries, Slides, Audio) to be generated directly
        from validated teacher courses without triggering redundant, expensive LLM calls.
        """
        sections = list(course.sections.filter(parent=None).order_by("order"))
        if not sections:
            sections = list(course.sections.all().order_by("order"))

        sections_outline: list[dict[str, Any]] = []
        all_objectives: list[dict[str, Any]] = []
        all_takeaways: list[str] = []

        for idx, sec in enumerate(sections, start=1):
            # Extract section objectives
            sec_objs = sec.objectives if isinstance(sec.objectives, list) else []
            for o_idx, o in enumerate(sec_objs, start=1):
                all_objectives.append({
                    "id": f"obj_{idx}_{o_idx}",
                    "taxonomy_level": "Comprendre",
                    "description": str(o),
                    "source_ref": f"Section {idx}",
                })

            # Check if summary has takeaways
            if sec.summary and sec.summary.strip():
                all_takeaways.append(sec.summary.strip())

            sections_outline.append({
                "order": idx,
                "title": sec.title,
                "key_explanation": sec.content,
                "source_facts": [sec.content[:300]] if sec.content else [],
                "pedagogical_examples": [],
                "summary": sec.summary,
                "estimated_minutes": sec.estimated_minutes,
            })

        # Extract concepts from title & content
        concepts: list[dict[str, Any]] = []
        for s in sections_outline:
            # Generate key concepts heuristically from section titles
            clean_title = re.sub(r"^(?:Chapitre|Section|Leçon|\d+[\.\:\-])\s*", "", s["title"], flags=re.IGNORECASE).strip()
            if clean_title and len(clean_title) > 3:
                concepts.append({
                    "term": clean_title,
                    "canonical_definition": s["summary"] or s["key_explanation"][:200] or f"Notion centrale de {clean_title}",
                    "importance": "CORE",
                    "source_ref": f"Section {s['order']}",
                })

        normalized = self.validator.validate_and_normalize({
            "title": course.title,
            "subject": course.title,
            "target_audience": "Étudiants et apprenants",
            "level": course.level,
            "learning_objectives": all_objectives,
            "key_concepts": concepts,
            "sections_outline": sections_outline,
            "key_takeaways": all_takeaways,
            "source_references": [{"course_id": str(course.id), "title": course.title}],
            "metadata": {"course_id": str(course.id), "document_id": str(course.document_id) if course.document_id else None},
        })

        return PedagogicalBlueprint(**normalized)
