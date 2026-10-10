"""Deterministic Evaluators for Amanus Learn AI (Sprint 06).

Rule: Deterministic checks are hard, non-negotiable binary evaluations.
Failure on any deterministic metric results in an immediate failure of the evaluation step.
"""

import io
from typing import Any

from apps.ai.evaluation.base import EvaluationCategory, MetricResult
from apps.ai.evaluation.thresholds import ACCEPTANCE_THRESHOLDS
from apps.ai.services.orchestration.lifecycle import TaskLifecycleStatus
from apps.audio.services.audio_assembler import AudioAssembler
from apps.audio.services.text_processor import AudioTextSegmenter
from apps.quizzes.services.validator import QuizQuestionValidator


class CourseDeterministicEvaluator:
    """Evaluates deterministic structural and schema integrity of generated courses."""

    @classmethod
    def evaluate(cls, payload: Any, expected: dict[str, Any] | None = None) -> list[MetricResult]:
        metrics: list[MetricResult] = []
        expected = expected or {}

        # 1. Schema Validity: must be a non-empty dict
        is_dict = isinstance(payload, dict) and bool(payload)
        metrics.append(
            MetricResult(
                name="course_schema_validity",
                value=is_dict,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=is_dict,
                explanation="Le cours généré doit être un dictionnaire JSON valide non vide.",
            )
        )
        if not is_dict:
            return metrics

        # 2. Mandatory Fields: title, description, chapters
        title = payload.get("title")
        has_title = isinstance(title, str) and bool(title.strip())
        description = payload.get("description")
        has_desc = isinstance(description, str) and bool(description.strip())
        chapters = payload.get("chapters")
        has_chapters = isinstance(chapters, list) and len(chapters) > 0

        mandatory_fields_pass = bool(has_title and has_desc and has_chapters)
        metrics.append(
            MetricResult(
                name="course_mandatory_fields",
                value=mandatory_fields_pass,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=mandatory_fields_pass,
                explanation="Les champs 'title', 'description' et 'chapters' doivent être présents et valides.",
                details={
                    "has_title": has_title,
                    "has_desc": has_desc,
                    "has_chapters": has_chapters,
                },
            )
        )

        if not has_chapters:
            return metrics

        # 3. Chapter Content & Monotonicity
        empty_content_found = False
        chapter_count = len(chapters)
        min_chapters_target = expected.get("min_chapters", 1)
        chapter_count_pass = chapter_count >= min_chapters_target

        for chap in chapters:
            if not isinstance(chap, dict):
                empty_content_found = True
                break
            chap_title = chap.get("title")
            if not chap_title or not str(chap_title).strip():
                empty_content_found = True
            sections = chap.get("sections") or chap.get("lessons") or []
            if not sections:
                empty_content_found = True
            for sec in sections:
                if not isinstance(sec, dict):
                    empty_content_found = True
                    break
                sec_title = sec.get("title")
                sec_content = sec.get("content")
                if (
                    not sec_title
                    or not str(sec_title).strip()
                    or not sec_content
                    or not str(sec_content).strip()
                ):
                    empty_content_found = True

        metrics.append(
            MetricResult(
                name="course_chapter_count_compliance",
                value=chapter_count,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=min_chapters_target,
                passed=chapter_count_pass,
                explanation=f"Nombre de chapitres générés ({chapter_count}) conforme à l'attendu (min: {min_chapters_target}).",
            )
        )

        metrics.append(
            MetricResult(
                name="course_empty_content_forbidden",
                value=not empty_content_found,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=not empty_content_found,
                explanation="Aucun titre ou contenu de chapitre/section ne doit être vide.",
            )
        )

        return metrics


class SlidesDeterministicEvaluator:
    """Evaluates deterministic properties of presentation decks and OpenXML/PPTX exports."""

    @classmethod
    def evaluate(
        self,
        payload: Any,
        expected: dict[str, Any] | None = None,
        pptx_bytes: bytes | None = None,
    ) -> list[MetricResult]:
        metrics: list[MetricResult] = []
        expected = expected or {}

        # 1. Presentation Structure Validity
        is_dict = isinstance(payload, dict) and bool(payload)
        metrics.append(
            MetricResult(
                name="slides_schema_validity",
                value=is_dict,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=is_dict,
                explanation="La présentation générée doit être un dictionnaire structuré.",
            )
        )
        if not is_dict:
            return metrics

        # 2. Slide count compliance
        slides = payload.get("slides") or []
        slide_count = len(slides)
        exact_target = expected.get("exact_slide_count")
        slide_count_passed = True if exact_target is None else (slide_count == exact_target)

        metrics.append(
            MetricResult(
                name="slides_count_compliance",
                value=slide_count,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=exact_target if exact_target is not None else 1,
                passed=slide_count_passed,
                explanation=f"Nombre de slides ({slide_count}) conforme au besoin (attendu: {exact_target}).",
            )
        )

        # 3. Density validation per slide
        density_violation = False
        max_bullets_threshold = ACCEPTANCE_THRESHOLDS["slides"]["deterministic"][
            "max_bullets_per_slide"
        ]
        max_chars_threshold = ACCEPTANCE_THRESHOLDS["slides"]["deterministic"][
            "max_chars_per_bullet"
        ]

        for slide in slides:
            if not isinstance(slide, dict):
                density_violation = True
                continue
            bullets = slide.get("bullet_points") or []
            if len(bullets) > max_bullets_threshold:
                density_violation = True
            for b in bullets:
                if len(str(b)) > max_chars_threshold:
                    density_violation = True

        metrics.append(
            MetricResult(
                name="slides_density_limits_respected",
                value=not density_violation,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=not density_violation,
                explanation=f"Chaque slide doit contenir au plus {max_bullets_threshold} puces de max {max_chars_threshold} caractères.",
            )
        )

        # 4. PPTX Binary Validation if bytes provided
        if pptx_bytes is not None:
            pptx_valid = False
            error_msg = ""
            try:
                from pptx import Presentation

                prs = Presentation(io.BytesIO(pptx_bytes))
                pptx_valid = len(prs.slides) >= 0
            except Exception as e:
                pptx_valid = False
                error_msg = str(e)

            metrics.append(
                MetricResult(
                    name="pptx_binary_integrity",
                    value=pptx_valid,
                    category=EvaluationCategory.DETERMINISTIC,
                    target_threshold=True,
                    passed=pptx_valid,
                    explanation="Le fichier PPTX produit doit être un conteneur OpenXML lisible et non corrompu.",
                    details={"error": error_msg},
                )
            )

        return metrics


class AudioDeterministicEvaluator:
    """Evaluates deterministic audio validity, magic headers, and text segmentation fidelity."""

    @classmethod
    def evaluate(
        cls,
        audio_bytes: bytes | None,
        source_text: str | None = None,
        expected: dict[str, Any] | None = None,
    ) -> list[MetricResult]:
        metrics: list[MetricResult] = []
        expected = expected or {}

        # 1. Byte Stream & Magic Header
        has_bytes = bool(audio_bytes and len(audio_bytes) >= AudioAssembler.MIN_AUDIO_BYTES)
        is_magic_valid = False
        if has_bytes and audio_bytes is not None:
            is_id3 = audio_bytes.startswith(b"ID3")
            is_mpeg_frame = any(
                audio_bytes.startswith(sync) for sync in AudioAssembler.MPEG_SYNC_BYTES
            )
            is_magic_valid = is_id3 or is_mpeg_frame

        metrics.append(
            MetricResult(
                name="audio_magic_header_valid",
                value=is_magic_valid,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=is_magic_valid,
                explanation="Le flux audio doit débuter par un en-tête ID3 ou un mot de synchronisation MPEG valide.",
            )
        )

        metrics.append(
            MetricResult(
                name="audio_min_size_satisfied",
                value=len(audio_bytes) if audio_bytes else 0,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=AudioAssembler.MIN_AUDIO_BYTES,
                passed=has_bytes,
                explanation=f"La taille audio doit être d'au moins {AudioAssembler.MIN_AUDIO_BYTES} octets.",
            )
        )

        # 2. Text Segmentation Fidelity (Zero loss, zero duplication)
        if source_text:
            chunks = AudioTextSegmenter.segment_text(source_text)
            orig_words = source_text.strip().split()
            reassembled_words = (" ".join(chunks)).strip().split()

            zero_loss = orig_words == reassembled_words
            metrics.append(
                MetricResult(
                    name="audio_text_preservation_fidelity",
                    value=zero_loss,
                    category=EvaluationCategory.DETERMINISTIC,
                    target_threshold=True,
                    passed=zero_loss,
                    explanation="100% des mots du texte source doivent être préservés sans altération ni duplication.",
                    details={
                        "original_word_count": len(orig_words),
                        "reassembled_word_count": len(reassembled_words),
                        "chunk_count": len(chunks),
                    },
                )
            )

        return metrics


class QuizDeterministicEvaluator:
    """Evaluates strict deterministic criteria for multiple choice quiz questions."""

    @classmethod
    def evaluate(cls, questions: list[dict[str, Any]] | dict[str, Any]) -> list[MetricResult]:
        metrics: list[MetricResult] = []

        raw_list = questions.get("questions", []) if isinstance(questions, dict) else questions
        is_valid_list = isinstance(raw_list, list) and len(raw_list) > 0

        metrics.append(
            MetricResult(
                name="quiz_questions_list_valid",
                value=is_valid_list,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=is_valid_list,
                explanation="Le quiz doit contenir une liste non vide de questions.",
            )
        )
        if not is_valid_list:
            return metrics

        all_have_4_options = True
        all_have_single_correct = True
        all_have_distinct_options = True
        meta_distractor_detected = False
        explanations_valid = True

        for q in raw_list:
            answers = q.get("answers") or q.get("options") or []
            if len(answers) != 4:
                all_have_4_options = False

            correct_count = sum(1 for a in answers if bool(a.get("is_correct")))
            if correct_count != 1:
                all_have_single_correct = False

            texts = [str(a.get("text", "")).strip().lower() for a in answers]
            if len(set(texts)) != len(texts):
                all_have_distinct_options = False

            for t in texts:
                for banned in QuizQuestionValidator.BANNED_META_DISTRACTORS:
                    if banned in t:
                        meta_distractor_detected = True

            expl = str(q.get("explanation", "")).strip()
            if len(expl) < 10:
                explanations_valid = False

        metrics.append(
            MetricResult(
                name="quiz_exact_4_options_per_question",
                value=all_have_4_options,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=all_have_4_options,
                explanation="Chaque question de QCM doit proposer exactement 4 choix.",
            )
        )

        metrics.append(
            MetricResult(
                name="quiz_single_correct_answer_per_question",
                value=all_have_single_correct,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=all_have_single_correct,
                explanation="Chaque question doit comporter exactement une seule réponse correcte.",
            )
        )

        metrics.append(
            MetricResult(
                name="quiz_absence_of_meta_distractors",
                value=not meta_distractor_detected,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=not meta_distractor_detected,
                explanation="Aucun distracteur méta ('Toutes les réponses', 'None of the above') n'est toléré.",
            )
        )

        metrics.append(
            MetricResult(
                name="quiz_distinct_options",
                value=all_have_distinct_options,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=all_have_distinct_options,
                explanation="Les 4 options de chaque question doivent être mutuellement distinctes.",
            )
        )

        metrics.append(
            MetricResult(
                name="quiz_explanations_non_empty",
                value=explanations_valid,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=explanations_valid,
                explanation="Les explications pédagogiques doivent être complètes et faire plus de 10 caractères.",
            )
        )

        return metrics


class OrchestrationDeterministicEvaluator:
    """Evaluates deterministic orchestration state machine, isolation, and lock mechanics."""

    @classmethod
    def evaluate(cls, sample: dict[str, Any]) -> list[MetricResult]:
        metrics: list[MetricResult] = []

        status_str = sample.get("status")
        valid_status = status_str in {s.value for s in TaskLifecycleStatus}

        metrics.append(
            MetricResult(
                name="orchestration_status_enum_valid",
                value=valid_status,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=valid_status,
                explanation=f"Le statut '{status_str}' doit appartenir à l'énumération TaskLifecycleStatus.",
            )
        )

        multi_tenant_isolated = sample.get("tenant_isolation_enforced", True)
        metrics.append(
            MetricResult(
                name="orchestration_tenant_isolation_enforced",
                value=multi_tenant_isolated,
                category=EvaluationCategory.DETERMINISTIC,
                target_threshold=True,
                passed=multi_tenant_isolated,
                explanation="L'accès à une tâche doit être strictement restreint aux membres de l'organisation détentrice.",
            )
        )

        return metrics
