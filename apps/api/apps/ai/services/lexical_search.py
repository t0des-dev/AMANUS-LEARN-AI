"""Lexical keyword and phrase search service for document chunks.

Enforces strict organization_id multi-tenant isolation.
Supports exact term matching, acronyms, technical identifiers, and structural title boosts.
"""

import logging
import math
import re
from typing import Any

from django.db.models import Q

from apps.ingestion.models import DocumentChunk

logger = logging.getLogger(__name__)


def extract_search_terms(query: str) -> tuple[list[str], list[str]]:
    """Extracts exact phrases (enclosed in quotes) and individual keyword tokens."""
    if not query:
        return [], []

    # 1. Extract quoted exact phrases: "frank rosenblatt", "resnet-50"
    phrases = re.findall(r'"([^"]+)"', query)
    cleaned_query = re.sub(r'"[^"]+"', " ", query)

    # 2. Extract keyword tokens (length >= 2)
    raw_tokens = re.findall(r"\b[\w\-]{2,}\b", cleaned_query.lower())
    stopwords = {
        "les", "des", "une", "dans", "pour", "par", "avec", "sur", "est", "sont",
        "the", "and", "for", "with", "from", "that", "this", "what", "which",
    }
    keywords = [w for w in raw_tokens if w not in stopwords]

    return [p.strip().lower() for p in phrases if p.strip()], keywords


class LexicalSearchService:
    """Executes deterministic keyword and phrase matching across DocumentChunk records."""

    def search(
        self,
        query: str,
        organization_id: str,
        document_id: str | None = None,
        top_k: int = 10,
        min_score: float = 0.05,
    ) -> list[dict[str, Any]]:
        """Executes lexical search with organization multi-tenant filtering."""
        if not organization_id:
            raise ValueError("organization_id est obligatoire pour exécuter une recherche lexicale.")

        if not query or len(query.strip()) < 2:
            return []

        phrases, keywords = extract_search_terms(query)
        all_terms = phrases + keywords
        if not all_terms:
            return []

        # Strict tenant isolation
        qs = DocumentChunk.objects.filter(
            document__organization_id=organization_id,
        ).select_related("document", "page")

        if document_id:
            qs = qs.filter(document_id=document_id)

        # Build database filter for candidates matching any term
        q_filter = Q()
        for term in all_terms:
            q_filter |= Q(content__icontains=term) | Q(document__title__icontains=term)

        candidates = list(qs.filter(q_filter)[: top_k * 4])
        if not candidates:
            return []

        scored_candidates: list[tuple[DocumentChunk, float]] = []

        for chunk in candidates:
            content_lower = chunk.content.lower()
            meta = chunk.metadata or {}
            title_lower = chunk.document.title.lower()
            chapter_lower = str(meta.get("chapter") or "").lower()
            section_lower = str(meta.get("section") or "").lower()

            score = 0.0

            # 1. Exact phrase matches (High weight)
            for phrase in phrases:
                if phrase in content_lower:
                    score += 0.50
                if phrase in title_lower or phrase in chapter_lower or phrase in section_lower:
                    score += 0.25

            # 2. Keyword frequency matches
            matched_keywords = 0
            for kw in keywords:
                # Count occurrences in content
                count = content_lower.count(kw)
                if count > 0:
                    matched_keywords += 1
                    # Sub-linear term frequency saturation
                    score += 0.15 * math.log(1 + count)

                # Title / Heading boost
                if kw in title_lower or kw in chapter_lower or kw in section_lower:
                    score += 0.10

            # Coverage ratio bonus
            if keywords:
                coverage = matched_keywords / len(keywords)
                score += coverage * 0.20

            # Normalize score into [0.0, 1.0]
            normalized_score = min(1.0, round(score, 4))
            if normalized_score >= min_score:
                scored_candidates.append((chunk, normalized_score))

        # Sort descending by lexical score
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_results = scored_candidates[:top_k]

        return [
            self._format_result(chunk, score=score)
            for chunk, score in top_results
        ]

    def _format_result(self, chunk: DocumentChunk, score: float) -> dict[str, Any]:
        """Formats DocumentChunk into standardized search result dictionary."""
        meta = chunk.metadata or {}
        page_num = chunk.page.page_number if chunk.page else meta.get("page_number")

        return {
            "chunk_id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "document_title": chunk.document.title,
            "page": page_num,
            "page_number": page_num,
            "chapter": meta.get("chapter"),
            "section": meta.get("section"),
            "subsection": meta.get("subsection"),
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "score": score,
            "distance": round(1.0 - score, 4),
            "match_type": "lexical",
            "metadata": meta,
        }
