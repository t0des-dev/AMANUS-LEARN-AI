"""A/B and Version Comparison Engine for AI Generations (Sprint 06).

Compares baseline generations against improved candidates to measure empirical differences:
- Citation grounding improvements.
- Redundancy reductions.
- Token efficiency and cost variations.
- Non-regression verification (flags if any deterministic or semantic metric degraded).
"""

from dataclasses import dataclass, field
from typing import Any

from apps.ai.evaluation.base import EvaluationCategory, GeneratorEvaluationReport


@dataclass
class MetricComparison:
    """Comparison of a single metric between baseline and candidate."""

    metric_name: str
    category: str
    baseline_value: float | int | bool | str
    candidate_value: float | int | bool | str
    delta: float | None = None
    improved: bool = False
    regressed: bool = False
    details: str = ""


@dataclass
class VersionComparisonReport:
    """Consolidated report comparing two generation versions."""

    baseline_version: str
    candidate_version: str
    generator_type: str
    regressions_detected: bool
    summary: str
    metric_comparisons: list[MetricComparison] = field(default_factory=list)
    token_cost_comparison: dict[str, Any] = field(default_factory=dict)
    deterministic_regression_count: int = 0
    semantic_improvement_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "baseline_version": self.baseline_version,
            "candidate_version": self.candidate_version,
            "generator_type": self.generator_type,
            "regressions_detected": self.regressions_detected,
            "deterministic_regression_count": self.deterministic_regression_count,
            "semantic_improvement_count": self.semantic_improvement_count,
            "summary": self.summary,
            "metric_comparisons": [
                {
                    "metric_name": m.metric_name,
                    "category": m.category,
                    "baseline_value": m.baseline_value,
                    "candidate_value": m.candidate_value,
                    "delta": m.delta,
                    "improved": m.improved,
                    "regressed": m.regressed,
                    "details": m.details,
                }
                for m in self.metric_comparisons
            ],
            "token_cost_comparison": self.token_cost_comparison,
        }


class PromptVersionComparator:
    """Scientifically compares baseline prompt/model output against candidate prompt/model."""

    @classmethod
    def compare_reports(
        cls,
        baseline_report: GeneratorEvaluationReport,
        candidate_report: GeneratorEvaluationReport,
        generator_type: str = "all",
    ) -> VersionComparisonReport:
        metric_comparisons: list[MetricComparison] = []
        deterministic_regressions = 0
        semantic_improvements = 0

        # Build map of baseline metrics by sample_id and metric_name
        base_map: dict[str, dict[str, Any]] = {}
        for r in baseline_report.results:
            for m in r.metrics:
                key = f"{r.sample_id}::{m.name}"
                base_map[key] = {
                    "value": m.value,
                    "passed": m.passed,
                    "category": m.category.value
                    if hasattr(m.category, "value")
                    else str(m.category),
                }

        # Compare with candidate metrics
        for r in candidate_report.results:
            for m in r.metrics:
                key = f"{r.sample_id}::{m.name}"
                base_info = base_map.get(key)
                if not base_info:
                    continue

                b_val = base_info["value"]
                c_val = m.value
                category = base_info["category"]

                delta = None
                improved = False
                regressed = False

                if isinstance(b_val, bool) and isinstance(c_val, bool):
                    if b_val is True and c_val is False:
                        regressed = True
                        if category == EvaluationCategory.DETERMINISTIC.value:
                            deterministic_regressions += 1
                    elif b_val is False and c_val is True:
                        improved = True
                elif isinstance(b_val, (int, float)) and isinstance(c_val, (int, float)):
                    delta = round(float(c_val) - float(b_val), 4)
                    # Higher is better for citation, language, legibility
                    if "redundancy" in m.name or "overflow" in m.name:
                        improved = delta < 0
                        regressed = delta > 0
                    else:
                        improved = delta > 0
                        regressed = delta < 0

                    if regressed and category == EvaluationCategory.DETERMINISTIC.value:
                        deterministic_regressions += 1

                if improved and category == EvaluationCategory.SEMANTIC.value:
                    semantic_improvements += 1

                metric_comparisons.append(
                    MetricComparison(
                        metric_name=f"{r.sample_id}::{m.name}",
                        category=category,
                        baseline_value=b_val,
                        candidate_value=c_val,
                        delta=delta,
                        improved=improved,
                        regressed=regressed,
                        details=m.explanation,
                    )
                )

        has_regressions = deterministic_regressions > 0 or any(
            m.regressed for m in metric_comparisons
        )

        # Summary text
        summary = (
            f"Comparaison entre {baseline_report.version} et {candidate_report.version} : "
            f"{'RÉGRESSION DÉTECTÉE' if has_regressions else 'AUCUNE RÉGRESSION DÉTECTÉE'}. "
            f"{semantic_improvements} métrique(s) sémantique(s) améliorée(s), "
            f"{deterministic_regressions} régression(s) déterministe(s)."
        )

        return VersionComparisonReport(
            baseline_version=baseline_report.version,
            candidate_version=candidate_report.version,
            generator_type=generator_type,
            regressions_detected=has_regressions,
            summary=summary,
            metric_comparisons=metric_comparisons,
            deterministic_regression_count=deterministic_regressions,
            semantic_improvement_count=semantic_improvements,
        )
