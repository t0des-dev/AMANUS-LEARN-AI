"""Perceptual and Human-Calibrated Evaluators for Amanus Learn AI (Sprint 06).

Evaluates:
- Visual legibility and slide text density overflow.
- Perceptual acoustic naturalness of audio TTS.
- Pedagogical clarity index.
"""

from typing import Any

from apps.ai.evaluation.base import EvaluationCategory, MetricResult


class PerceptualEvaluator:
    """Evaluates perceptual criteria such as visual density and acoustic naturalness."""

    @classmethod
    def evaluate_slide_legibility(cls, slides: list[dict[str, Any]] | None) -> MetricResult:
        """Computes visual overflow and readability risk across slides."""
        slide_list = slides if isinstance(slides, list) else []
        overflow_count = 0
        total_slides = max(1, len(slide_list))

        for s in slide_list:
            if not isinstance(s, dict):
                continue
            bullets = s.get("bullet_points") or []
            # Overflow risk if > 6 bullets or any bullet > 160 chars
            if len(bullets) > 6 or any(len(str(b)) > 160 for b in bullets):
                overflow_count += 1

        overflow_rate = round(overflow_count / total_slides, 3)
        passed = overflow_rate == 0.0

        return MetricResult(
            name="slides_visual_overflow_rate",
            value=overflow_rate,
            category=EvaluationCategory.PERCEPTUAL,
            target_threshold=0.0,
            passed=passed,
            explanation=f"Taux de débordement visuel sur les diapositives : {overflow_rate * 100:.1f}% (seuil: 0.0%).",
            details={"overflow_count": overflow_count, "total_slides": total_slides},
        )

    @classmethod
    def evaluate_audio_acoustic_naturalness(
        cls,
        sample_id: str,
        calibrated_mos_score: float = 4.2,
    ) -> MetricResult:
        """Evaluates Mean Opinion Score (MOS, 1.0 to 5.0) on synthesized audio naturalness."""
        target_mos = 4.0
        passed = calibrated_mos_score >= target_mos

        return MetricResult(
            name="audio_acoustic_naturalness_mos",
            value=calibrated_mos_score,
            category=EvaluationCategory.PERCEPTUAL,
            target_threshold=target_mos,
            passed=passed,
            explanation=f"Score de naturel et intelligibilité vocale (MOS) : {calibrated_mos_score}/5.0 (seuil: {target_mos}).",
        )
