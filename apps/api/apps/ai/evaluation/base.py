"""Core data structures and base classes for generation evaluation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EvaluationCategory(str, Enum):
    """Classification of evaluation types to avoid mixing distinct evaluation dimensions."""

    DETERMINISTIC = "deterministic"  # Hard structural and schema checks
    SEMANTIC = "semantic"  # Content relevance, pedagogical quality, grounding
    PERCEPTUAL = "perceptual"  # Visual layout, acoustic quality, human rating


@dataclass
class MetricResult:
    """Represents a single evaluated metric."""

    name: str
    value: float | int | bool | str
    category: EvaluationCategory
    target_threshold: float | int | bool | str | None
    passed: bool
    explanation: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "category": self.category.value
            if isinstance(self.category, EvaluationCategory)
            else str(self.category),
            "target_threshold": self.target_threshold,
            "passed": self.passed,
            "explanation": self.explanation,
            "details": self.details,
        }


@dataclass
class EvaluationResult:
    """Consolidated evaluation result for a single sample or generation."""

    generator_type: str
    sample_id: str
    passed: bool
    metrics: list[MetricResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    telemetry: dict[str, Any] = field(default_factory=dict)  # tokens, duration_ms, bytes, cost_usd
    timestamp: str = ""

    @property
    def deterministic_passed(self) -> bool:
        """True only if every deterministic metric in this result passed."""
        det_metrics = [m for m in self.metrics if m.category == EvaluationCategory.DETERMINISTIC]
        return all(m.passed for m in det_metrics) if det_metrics else True

    @property
    def semantic_passed(self) -> bool:
        """True if all semantic metrics passed."""
        sem_metrics = [m for m in self.metrics if m.category == EvaluationCategory.SEMANTIC]
        return all(m.passed for m in sem_metrics) if sem_metrics else True

    @property
    def perceptual_passed(self) -> bool:
        """True if all perceptual metrics passed."""
        perc_metrics = [m for m in self.metrics if m.category == EvaluationCategory.PERCEPTUAL]
        return all(m.passed for m in perc_metrics) if perc_metrics else True

    def to_dict(self) -> dict[str, Any]:
        return {
            "generator_type": self.generator_type,
            "sample_id": self.sample_id,
            "passed": self.passed,
            "deterministic_passed": self.deterministic_passed,
            "semantic_passed": self.semantic_passed,
            "perceptual_passed": self.perceptual_passed,
            "metrics": [m.to_dict() for m in self.metrics],
            "errors": self.errors,
            "telemetry": self.telemetry,
            "timestamp": self.timestamp,
        }


@dataclass
class GeneratorEvaluationReport:
    """Aggregated evaluation report across multiple benchmark samples."""

    suite_name: str
    version: str
    total_samples: int
    passed_samples: int
    failed_samples: int
    results: list[EvaluationResult] = field(default_factory=list)
    summary_by_category: dict[str, Any] = field(default_factory=dict)
    telemetry_summary: dict[str, Any] = field(default_factory=dict)
    unsupported_or_skipped_evaluations: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""

    @property
    def success_rate(self) -> float:
        if self.total_samples == 0:
            return 1.0
        return round(self.passed_samples / self.total_samples, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite_name": self.suite_name,
            "version": self.version,
            "total_samples": self.total_samples,
            "passed_samples": self.passed_samples,
            "failed_samples": self.failed_samples,
            "success_rate": self.success_rate,
            "summary_by_category": self.summary_by_category,
            "telemetry_summary": self.telemetry_summary,
            "unsupported_or_skipped_evaluations": self.unsupported_or_skipped_evaluations,
            "results": [r.to_dict() for r in self.results],
            "generated_at": self.generated_at,
        }
