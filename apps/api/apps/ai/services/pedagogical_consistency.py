import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from apps.ai.services.pedagogical_blueprint import (
    PedagogicalBlueprint,
    PedagogicalBlueprintService,
)

logger = logging.getLogger(__name__)


@dataclass
class ConsistencyReport:
    """Detailed report on pedagogical alignment between course and derived content."""

    is_valid: bool
    score: float  # Normalized between 0.0 and 1.0
    format_name: str
    covered_concepts: list[str] = field(default_factory=list)
    missing_concepts: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "score": round(self.score, 3),
            "format_name": self.format_name,
            "covered_concepts": self.covered_concepts,
            "missing_concepts": self.missing_concepts,
            "issues": self.issues,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }


class PedagogicalConsistencyValidator:
    """Validates cross-modal pedagogical coherence and consistency between

    the source Course (or PedagogicalBlueprint) and derived formats:
    - Summaries (very_short, synthetic, detailed)
    - Quizzes / QCM
    - Slides / Presentations
    - Audio scripts
    """

    FORBIDDEN_AUDIO_VISUAL_PATTERNS = [
        re.compile(r"\bvoir\s+(?:ci-dessus|ci-dessous|la\s+figure|le\s+sch[ée]ma|le\s+tableau)\b", re.IGNORECASE),
        re.compile(r"\bcomme\s+illustr[ée](?:\s+ci-(?:dessus|dessous))?\b", re.IGNORECASE),
        re.compile(r"\ble\s+tableau\s+ci-(?:contre|dessous|dessus)\b", re.IGNORECASE),
        re.compile(r"\bsee\s+(?:above|below|figure|diagram|table)\b", re.IGNORECASE),
        re.compile(r"\bas\s+(?:shown|illustrated)\s+(?:above|below)\b", re.IGNORECASE),
        re.compile(r"\b(?:انظر|راجع)\s+(?:أعلاه|أدناه|الجدول|الشكل)\b", re.IGNORECASE),
    ]

    def __init__(self, min_concept_coverage: float = 0.50):
        self.min_concept_coverage = min_concept_coverage

    def _resolve_blueprint(self, course_or_blueprint: Any) -> PedagogicalBlueprint:
        if isinstance(course_or_blueprint, PedagogicalBlueprint):
            return course_or_blueprint
        return PedagogicalBlueprintService.derive_from_course(course_or_blueprint)

    def _tokenize_text(self, text: str) -> set[str]:
        if not text:
            return set()
        clean = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text.lower())
        return {w for w in clean.split() if len(w) > 2}

    def _extract_concepts(self, blueprint: PedagogicalBlueprint) -> list[str]:
        concepts = []
        for c in blueprint.key_concepts:
            term = c.get("term", "") if isinstance(c, dict) else getattr(c, "term", "")
            if term:
                concepts.append(term)
        return concepts

    def _extract_sections(self, blueprint: PedagogicalBlueprint) -> list[str]:
        sections = []
        for s in blueprint.sections:
            title = s.get("title", "") if isinstance(s, dict) else getattr(s, "title", "")
            if title:
                sections.append(title)
        return sections

    def validate_course_and_summary_alignment(
        self,
        course_or_blueprint: Any,
        summary_text: str,
        summary_level: str = "synthetic",
    ) -> ConsistencyReport:
        """Verifies that a generated summary faithfully represents the core concepts

        and objectives from the blueprint/course.
        """
        blueprint = self._resolve_blueprint(course_or_blueprint)
        summary_tokens = self._tokenize_text(summary_text)

        if not summary_tokens:
            return ConsistencyReport(
                is_valid=False,
                score=0.0,
                format_name="summary",
                issues=["Le résumé fourni est vide ou sans contenu textuel exploitable."],
                warnings=[],
            )

        key_concepts = self._extract_concepts(blueprint)
        covered: list[str] = []
        missing: list[str] = []

        STOP_WORDS = {
            "pour", "dans", "avec", "cette", "leurs", "sont", "leur", "introduction",
            "chapitre", "section", "partie", "module", "notions", "bases", "patterns", "pattern",
        }

        summary_lower = summary_text.lower()
        for concept in key_concepts:
            concept_clean = concept.strip().lower()
            if concept_clean in summary_lower:
                covered.append(concept)
                continue
            significant = [
                w for w in re.findall(r"[\w\u0600-\u06FF]+", concept_clean)
                if len(w) > 3 and w not in STOP_WORDS
            ]
            if significant and any(w in summary_tokens for w in significant):
                covered.append(concept)
            elif all(w in summary_tokens for w in concept_clean.split()):
                covered.append(concept)
            else:
                missing.append(concept)

        total_concepts = len(key_concepts)
        coverage_rate = (len(covered) / total_concepts) if total_concepts > 0 else 1.0

        issues: list[str] = []
        warnings: list[str] = []

        # Length check according to summary level
        word_count = len(summary_text.split())
        if summary_level == "very_short":
            if word_count > 150:
                warnings.append(
                    f"Le résumé 'very_short' est un peu long ({word_count} mots au lieu de ~100 max)."
                )
            threshold = min(self.min_concept_coverage, 0.30)
        elif summary_level == "detailed":
            if word_count < 100:
                issues.append(
                    f"Le résumé 'detailed' est trop succinct ({word_count} mots) pour un niveau détaillé."
                )
            threshold = 0.60
        else:
            threshold = self.min_concept_coverage

        if coverage_rate < threshold:
            issues.append(
                f"Couverture conceptuelle insuffisante ({coverage_rate:.1%} < seuil {threshold:.1%}). "
                f"Concepts manquants : {', '.join(missing[:5])}"
            )

        is_valid = len(issues) == 0
        return ConsistencyReport(
            is_valid=is_valid,
            score=coverage_rate,
            format_name="summary",
            covered_concepts=covered,
            missing_concepts=missing,
            issues=issues,
            warnings=warnings,
            metadata={"summary_level": summary_level, "word_count": word_count},
        )

    def validate_course_and_quiz_alignment(
        self,
        course_or_blueprint: Any,
        questions: list[Any],
    ) -> ConsistencyReport:
        """Verifies that quiz questions assess key objectives and concepts

        without introducing alien, unsupported concepts.
        """
        blueprint = self._resolve_blueprint(course_or_blueprint)
        if not questions:
            return ConsistencyReport(
                is_valid=False,
                score=0.0,
                format_name="quiz",
                issues=["Aucune question fournie pour la validation de cohérence."],
            )

        key_concepts = self._extract_concepts(blueprint)
        covered_concepts: set[str] = set()
        issues: list[str] = []
        warnings: list[str] = []

        valid_question_count = 0
        for idx, q in enumerate(questions):
            q_text = getattr(q, "text", "") or (q.get("text") if isinstance(q, dict) else "")
            q_expl = getattr(q, "explanation", "") or (q.get("explanation") if isinstance(q, dict) else "")

            combined_q = f"{q_text} {q_expl}".lower()
            # Check concept coverage
            for concept in key_concepts:
                if concept.lower() in combined_q:
                    covered_concepts.add(concept)

            # Check for non-empty text
            if len(q_text.strip()) < 10:
                issues.append(f"Question #{idx + 1} a un énoncé trop court ({len(q_text)} caractères).")
                continue

            valid_question_count += 1

        total_concepts = len(key_concepts)
        concept_score = (len(covered_concepts) / total_concepts) if total_concepts > 0 else 1.0

        if valid_question_count == 0:
            issues.append("Toutes les questions fournies sont invalides.")

        is_valid = len(issues) == 0
        return ConsistencyReport(
            is_valid=is_valid,
            score=concept_score,
            format_name="quiz",
            covered_concepts=list(covered_concepts),
            missing_concepts=[c for c in key_concepts if c not in covered_concepts],
            issues=issues,
            warnings=warnings,
            metadata={"question_count": len(questions), "valid_count": valid_question_count},
        )

    def validate_course_and_slides_alignment(
        self,
        course_or_blueprint: Any,
        slides_data: list[dict[str, Any]],
    ) -> ConsistencyReport:
        """Verifies that slides align with course structure, have meaningful titles,

        and maintain reasonable bullet density without text overload.
        """
        blueprint = self._resolve_blueprint(course_or_blueprint)
        if not slides_data:
            return ConsistencyReport(
                is_valid=False,
                score=0.0,
                format_name="slides",
                issues=["Aucune diapositive fournie."],
            )

        issues: list[str] = []
        warnings: list[str] = []
        covered_sections: set[str] = set()
        section_titles = self._extract_sections(blueprint)

        for idx, slide in enumerate(slides_data):
            title = slide.get("title", "").strip()
            if not title:
                issues.append(f"Diapositive #{idx + 1} n'a pas de titre.")

            # Check bullet overload (> 8 bullets is considered an overloaded slide)
            bullets = slide.get("bullets", [])
            if len(bullets) > 8:
                warnings.append(
                    f"Diapositive #{idx + 1} ({title}) présente une surcharge textuelle ({len(bullets)} puces)."
                )

            # Match section title
            for sec_title in section_titles:
                if sec_title.lower() in title.lower() or title.lower() in sec_title.lower():
                    covered_sections.add(sec_title)

        total_sections = len(section_titles)
        section_coverage = (len(covered_sections) / total_sections) if total_sections > 0 else 1.0

        is_valid = len(issues) == 0
        return ConsistencyReport(
            is_valid=is_valid,
            score=section_coverage,
            format_name="slides",
            covered_concepts=list(covered_sections),
            missing_concepts=[s for s in section_titles if s not in covered_sections],
            issues=issues,
            warnings=warnings,
            metadata={"slide_count": len(slides_data)},
        )

    def validate_course_and_audio_alignment(
        self,
        course_or_blueprint: Any,
        audio_script: str,
    ) -> ConsistencyReport:
        """Verifies that an audio script is speech-ready:

        - Strictly contains NO forbidden visual references ("voir ci-dessus", etc.).
        - Covers key concepts in spoken narrative.
        """
        blueprint = self._resolve_blueprint(course_or_blueprint)
        if not audio_script or not audio_script.strip():
            return ConsistencyReport(
                is_valid=False,
                score=0.0,
                format_name="audio",
                issues=["Le script audio est vide."],
            )

        issues: list[str] = []
        warnings: list[str] = []

        # Check forbidden visual references
        for pattern in self.FORBIDDEN_AUDIO_VISUAL_PATTERNS:
            match = pattern.search(audio_script)
            if match:
                issues.append(
                    f"Référence visuelle inadaptée à l'écoute détectée : « {match.group(0)} »."
                )

        # Check raw markdown tables (| col | col |) that shouldn't be read out loud
        if re.search(r"\|.*\|.*\|", audio_script):
            issues.append("Un tableau markdown brut non converti a été détecté dans le script audio.")

        # Check concept coverage
        key_concepts = self._extract_concepts(blueprint)
        covered: list[str] = []
        missing: list[str] = []
        script_lower = audio_script.lower()

        for concept in key_concepts:
            if concept.lower() in script_lower:
                covered.append(concept)
            else:
                missing.append(concept)

        total = len(key_concepts)
        score = (len(covered) / total) if total > 0 else 1.0

        is_valid = len(issues) == 0
        return ConsistencyReport(
            is_valid=is_valid,
            score=score,
            format_name="audio",
            covered_concepts=covered,
            missing_concepts=missing,
            issues=issues,
            warnings=warnings,
            metadata={"script_length_chars": len(audio_script)},
        )

    def remediate_with_bounded_retry(
        self,
        generator_fn: Callable[[], Any],
        validator_fn: Callable[[Any], ConsistencyReport],
        max_retries: int = 1,
    ) -> tuple[Any, ConsistencyReport]:
        """Executes a generation with a strictly bounded remediation retry (max_retries <= 1)

        to avoid runaway loops and protect token quotas.
        """
        bounded_limit = min(max(0, max_retries), 1)

        result = generator_fn()
        report = validator_fn(result)

        if report.is_valid or bounded_limit == 0:
            return result, report

        logger.info(
            "Pedagogical consistency failed (%s). Triggering bounded retry (1/1): %s",
            report.format_name,
            "; ".join(report.issues),
        )

        # Bounded single retry
        try:
            remediated_result = generator_fn()
            remediated_report = validator_fn(remediated_result)
            if remediated_report.is_valid or remediated_report.score >= report.score:
                return remediated_result, remediated_report
        except Exception as exc:
            logger.warning("Bounded retry attempt failed: %s", exc)

        # If retry didn't improve or failed, return original with issues logged
        return result, report
