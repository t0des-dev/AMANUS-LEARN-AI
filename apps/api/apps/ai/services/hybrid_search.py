"""Hybrid search service combining semantic vector search and lexical keyword search.

Implements Reciprocal Rank Fusion (RRF) and deduplication for optimal retrieval
on educational and technical documents.
"""

import logging
from typing import Any

from .embeddings import EmbeddingProvider, get_embedding_provider
from .lexical_search import LexicalSearchService
from .reranker import Reranker
from .vector_search import VectorSearchService

logger = logging.getLogger(__name__)


class HybridSearchService:
    """Executes hybrid multi-stage retrieval:

    1. Semantic search (vector similarity via embeddings).
    2. Lexical search (exact terms, acronyms, and keywords).
    3. Reciprocal Rank Fusion (RRF) combining semantic and lexical ranks.
    4. Re-ranking with structural heading boosts and candidate deduplication.
    """

    def __init__(
        self,
        vector_search: VectorSearchService | None = None,
        lexical_search: LexicalSearchService | None = None,
        embedding_provider: EmbeddingProvider | None = None,
        reranker: Reranker | None = None,
        semantic_weight: float = 0.6,
        lexical_weight: float = 0.4,
        rrf_k: int = 60,
    ):
        self.vector_search = vector_search or VectorSearchService()
        self.lexical_search = lexical_search or LexicalSearchService()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.reranker = reranker or Reranker()
        self.semantic_weight = semantic_weight
        self.lexical_weight = lexical_weight
        self.rrf_k = rrf_k

    def search(
        self,
        query: str,
        organization_id: str,
        document_id: str | None = None,
        top_k: int = 5,
        candidate_k: int = 25,
        min_score: float = 0.0,
        query_vector: list[float] | None = None,
    ) -> list[dict[str, Any]]:
        """Executes hybrid search combining vector and lexical rankings with RRF."""
        if not query or len(query.strip()) < 2:
            return []

        # 1. Semantic Candidates with graceful fallback on embedding failure
        semantic_results = []
        try:
            if query_vector is None:
                query_vector = self.embedding_provider.embed_text(query)
            if query_vector:
                semantic_results = self.vector_search.search(
                    query_vector=query_vector,
                    organization_id=organization_id,
                    document_id=document_id,
                    top_k=candidate_k,
                )
        except Exception as e:
            logger.warning(f"[HybridSearch] Semantic search error, relying on lexical fallback: {e}")
            semantic_results = []

        # 2. Lexical Candidates
        lexical_results = self.lexical_search.search(
            query=query,
            organization_id=organization_id,
            document_id=document_id,
            top_k=candidate_k,
        )

        # 3. Reciprocal Rank Fusion (RRF)
        fused_chunks: dict[str, dict[str, Any]] = {}
        rrf_scores: dict[str, float] = {}

        # Add semantic ranks
        for rank, item in enumerate(semantic_results, start=1):
            chunk_id = item["chunk_id"]
            rrf_contrib = self.semantic_weight / (self.rrf_k + rank)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_contrib
            if chunk_id not in fused_chunks:
                fused_chunks[chunk_id] = dict(item)
                fused_chunks[chunk_id]["match_sources"] = ["semantic"]
            else:
                fused_chunks[chunk_id]["match_sources"].append("semantic")

        # Add lexical ranks
        for rank, item in enumerate(lexical_results, start=1):
            chunk_id = item["chunk_id"]
            rrf_contrib = self.lexical_weight / (self.rrf_k + rank)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + rrf_contrib
            if chunk_id not in fused_chunks:
                fused_chunks[chunk_id] = dict(item)
                fused_chunks[chunk_id]["match_sources"] = ["lexical"]
            else:
                if "lexical" not in fused_chunks[chunk_id]["match_sources"]:
                    fused_chunks[chunk_id]["match_sources"].append("lexical")

        if not fused_chunks:
            return []

        # Normalize RRF scores
        max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0
        candidate_list: list[dict[str, Any]] = []

        for chunk_id, chunk_data in fused_chunks.items():
            norm_score = round(rrf_scores[chunk_id] / max_rrf, 4) if max_rrf > 0 else 0.5
            chunk_data["score"] = norm_score
            chunk_data["rrf_score"] = round(rrf_scores[chunk_id], 6)
            candidate_list.append(chunk_data)

        # 4. Re-rank candidates using structural heading boosts
        reranked = self.reranker.rerank(query, candidate_list, top_k=top_k * 2)

        # 5. Deduplicate near-identical snippets
        final_results: list[dict[str, Any]] = []
        seen_contents: list[str] = []

        for item in reranked:
            if item["score"] < min_score:
                continue

            content = item.get("content", "").strip()
            # Simple deduplication check for overlapping chunks
            is_duplicate = False
            for prev in seen_contents:
                # If 80%+ overlap in content prefix
                if content in prev or prev in content:
                    is_duplicate = True
                    break

            if not is_duplicate:
                final_results.append(item)
                seen_contents.append(content)
                if len(final_results) >= top_k:
                    break

        return final_results
