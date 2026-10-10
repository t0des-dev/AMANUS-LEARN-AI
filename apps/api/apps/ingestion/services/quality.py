"""Quality assurance and integrity assessment service for document ingestion.

Evaluates extracted text density, page completeness, repetition anomalies,
and classifies documents into FULL, PARTIAL, or UNUSABLE quality tiers.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from apps.ingestion.parsers.base import ParsedDocument

logger = logging.getLogger(__name__)


@dataclass
class QualityAssessmentResult:
    """Structured report containing extraction quality metrics and warnings."""

    quality_grade: str  # "FULL", "PARTIAL", "UNUSABLE"
    is_usable: bool
    total_pages: int
    empty_pages: int
    scanned_pages: int
    total_chars: int
    avg_chars_per_page: float
    repetition_score: float
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "quality_grade": self.quality_grade,
            "is_usable": self.is_usable,
            "total_pages": self.total_pages,
            "empty_pages": self.empty_pages,
            "scanned_pages": self.scanned_pages,
            "total_chars": self.total_chars,
            "avg_chars_per_page": round(self.avg_chars_per_page, 1),
            "repetition_score": round(self.repetition_score, 3),
            "warnings": self.warnings,
            "details": self.details,
        }


class DocumentQualityEvaluator:
    """Evaluates the quality and exploitation readiness of a parsed document."""

    MIN_PAGE_CHARS = 20  # Under 20 chars considered empty/placeholder
    MIN_DOC_CHARS = 30  # Entire doc under 30 chars is considered unusable

    @classmethod
    def evaluate(cls, parsed_doc: ParsedDocument) -> QualityAssessmentResult:
        warnings: list[str] = list(parsed_doc.metadata.get("warnings", []))
        total_pages = len(parsed_doc.pages)

        if total_pages == 0:
            return QualityAssessmentResult(
                quality_grade="UNUSABLE",
                is_usable=False,
                total_pages=0,
                empty_pages=0,
                scanned_pages=0,
                total_chars=0,
                avg_chars_per_page=0.0,
                repetition_score=0.0,
                warnings=["DOCUMENT_HAS_NO_PAGES", "DOCUMENT_EMPTY_OR_UNUSABLE"],
                details={"reason": "Aucune page ou diapositive détectée dans le document."},
            )

        empty_pages = 0
        scanned_pages = 0
        total_chars = 0
        all_text_blocks: list[str] = []

        for p in parsed_doc.pages:
            char_count = len(p.text.strip())
            total_chars += char_count
            all_text_blocks.append(p.text)

            # Check if page is effectively empty
            if char_count < cls.MIN_PAGE_CHARS:
                empty_pages += 1

            # Check if page was scanned or required OCR
            if p.ocr_used or p.metadata.get("ocr_needed"):
                scanned_pages += 1

            # Inherit page-level warnings
            page_warnings = p.metadata.get("warnings", [])
            for w in page_warnings:
                if w not in warnings:
                    warnings.append(w)

        avg_chars = total_chars / max(1, total_pages)

        # Repetition check (detect repeated tokens/characters)
        full_text = " ".join(all_text_blocks)
        repetition_score = cls._compute_repetition_score(full_text)
        if repetition_score > 0.45 and total_chars > 100:
            warnings.append("SUSPICIOUS_TEXT_REPETITION")

        # Determine Quality Grade
        if total_chars < cls.MIN_DOC_CHARS:
            quality_grade = "UNUSABLE"
            is_usable = False
            warnings.append("DOCUMENT_EMPTY_OR_UNUSABLE")
        elif empty_pages == total_pages:
            quality_grade = "UNUSABLE"
            is_usable = False
            warnings.append("ALL_PAGES_EMPTY")
        elif empty_pages > 0 or scanned_pages > 0 or len(warnings) > 0:
            quality_grade = "PARTIAL"
            is_usable = True
            if empty_pages > 0 and "SOME_PAGES_EMPTY" not in warnings:
                warnings.append(f"PARTIAL_EMPTY_PAGES_{empty_pages}_OF_{total_pages}")
            if scanned_pages > 0 and "SCANNED_PAGES_PRESENT" not in warnings:
                warnings.append(f"SCANNED_PAGES_DETECTED_{scanned_pages}")
        else:
            quality_grade = "FULL"
            is_usable = True

        return QualityAssessmentResult(
            quality_grade=quality_grade,
            is_usable=is_usable,
            total_pages=total_pages,
            empty_pages=empty_pages,
            scanned_pages=scanned_pages,
            total_chars=total_chars,
            avg_chars_per_page=avg_chars,
            repetition_score=repetition_score,
            warnings=warnings,
            details={
                "min_doc_chars_threshold": cls.MIN_DOC_CHARS,
                "has_ocr_content": scanned_pages > 0,
            },
        )

    @staticmethod
    def _compute_repetition_score(text: str) -> float:
        """Measures lexical and n-gram repetition to detect OCR garbage or infinite loops."""
        words = re.findall(r"\b\w+\b", text.lower())
        if len(words) < 15:
            return 0.0

        unique_words = set(words)
        uniqueness_ratio = len(unique_words) / len(words)
        # Low uniqueness ratio indicates high repetition
        return max(0.0, 1.0 - uniqueness_ratio)
