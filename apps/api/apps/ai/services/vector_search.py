import logging
import math
from typing import Any

from django.db import connection

from apps.ingestion.models import DocumentChunk

logger = logging.getLogger(__name__)


def python_cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculates cosine similarity between two numeric vectors in pure Python."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorSearchService:
    """Executes high-performance vector similarity search against DocumentChunk embeddings.

    Supports native pgvector CosineDistance on PostgreSQL with seamless fallback
    for SQLite unit tests. Enforces strict organization_id multi-tenant isolation.
    """

    def search(
        self,
        query_vector: list[float],
        organization_id: str,
        document_id: str | None = None,
        top_k: int = 10,
        min_similarity: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Searches for chunks closest to query_vector within an organization."""
        if not organization_id:
            raise ValueError(
                "organization_id est obligatoire pour exécuter une recherche vectorielle."
            )

        # Strict tenant isolation
        qs = DocumentChunk.objects.filter(
            document__organization_id=organization_id,
            embedding__isnull=False,
        ).select_related("document", "page")

        if document_id:
            qs = qs.filter(document_id=document_id)

        results: list[dict[str, Any]] = []

        is_postgres = connection.vendor == "postgresql"

        if is_postgres:
            try:
                from pgvector.django import CosineDistance

                annotated_qs = qs.annotate(
                    distance=CosineDistance("embedding", query_vector)
                ).order_by("distance")[:top_k]

                for chunk in annotated_qs:
                    dist = getattr(chunk, "distance", 1.0)
                    sim = max(0.0, min(1.0, 1.0 - float(dist)))
                    if sim < min_similarity:
                        continue

                    results.append(self._format_result(chunk, score=sim, distance=dist))

                return results
            except Exception as e:
                logger.warning(
                    f"[VectorSearchService] Native pgvector failed ({e}), using in-memory fallback."
                )

        # In-memory vector calculation (SQLite unit tests or non-pg fallback)
        chunks = list(qs)
        scored_chunks: list[tuple[DocumentChunk, float]] = []

        for chunk in chunks:
            raw_emb = chunk.embedding
            if raw_emb is None:
                continue
            # Handle list or pgvector Vector object
            emb_list = list(raw_emb) if hasattr(raw_emb, "__iter__") else []
            sim = python_cosine_similarity(query_vector, emb_list)
            if sim >= min_similarity:
                scored_chunks.append((chunk, sim))

        # Sort descending by similarity
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_scored = scored_chunks[:top_k]

        for chunk, sim in top_scored:
            results.append(self._format_result(chunk, score=sim, distance=1.0 - sim))

        return results

    def _format_result(
        self,
        chunk: DocumentChunk,
        score: float,
        distance: float,
    ) -> dict[str, Any]:
        """Formats a DocumentChunk into a standardized search result dictionary."""
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
            "score": round(score, 4),
            "distance": round(distance, 4),
            "metadata": meta,
        }
