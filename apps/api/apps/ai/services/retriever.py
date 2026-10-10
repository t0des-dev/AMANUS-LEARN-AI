import hashlib
import logging
import time
from typing import Any

from django.core.cache import cache

from .citation_builder import CitationBuilder
from .context_builder import ContextBuilder
from .embeddings import EmbeddingProvider, get_embedding_provider
from .hybrid_search import HybridSearchService
from .lexical_search import LexicalSearchService
from .reranker import Reranker
from .vector_search import VectorSearchService

logger = logging.getLogger(__name__)


class Retriever:
    """Orchestrates the end-to-end RAG retrieval pipeline:

    Question -> Hybrid Search (pgvector + Lexical BM25/Exact RRF) -> Re-ranking -> Context -> Citations
    Supports search_mode: 'hybrid' (default), 'semantic', 'lexical'.
    Features strict tenant isolation, graceful fallback on embedding failure, and query caching with invalidation.
    """

    CACHE_TTL_SECONDS = 3600  # 1 hour

    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        vector_search: VectorSearchService | None = None,
        lexical_search: LexicalSearchService | None = None,
        hybrid_search: HybridSearchService | None = None,
        reranker: Reranker | None = None,
        context_builder: ContextBuilder | None = None,
        citation_builder: CitationBuilder | None = None,
    ):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.vector_search = vector_search or VectorSearchService()
        self.lexical_search = lexical_search or LexicalSearchService()
        self.hybrid_search = hybrid_search or HybridSearchService(
            vector_search=self.vector_search,
            lexical_search=self.lexical_search,
        )
        self.reranker = reranker or Reranker()
        self.context_builder = context_builder or ContextBuilder()
        self.citation_builder = citation_builder or CitationBuilder()

    @classmethod
    def get_version(cls, organization_id: str, document_id: str | None = None) -> int:
        """Retrieves active version counter for tenant/document to enable instant cache invalidation."""
        doc_key = document_id or "all"
        key = f"rag:ver:{organization_id}:{doc_key}"
        ver = cache.get(key)
        if ver is None:
            ver = 1
            cache.set(key, 1, timeout=86400 * 30)
        return int(ver)

    @classmethod
    def invalidate_cache(cls, organization_id: str, document_id: str | None = None) -> None:
        """Invalidates cached RAG queries for the given organization and document."""
        try:
            if document_id:
                doc_key = f"rag:ver:{organization_id}:{document_id}"
                try:
                    cache.incr(doc_key)
                except Exception:
                    curr = cache.get(doc_key, 1)
                    cache.set(doc_key, int(curr) + 1, timeout=86400 * 30)

            all_key = f"rag:ver:{organization_id}:all"
            try:
                cache.incr(all_key)
            except Exception:
                curr = cache.get(all_key, 1)
                cache.set(all_key, int(curr) + 1, timeout=86400 * 30)

            logger.info(f"[RAG Cache] Invalidated queries for org={organization_id}, doc={document_id}")
        except Exception as e:
            logger.warning(f"[RAG Cache] Failed to increment cache version: {e}")

    @classmethod
    def compute_cache_key(
        cls,
        organization_id: str,
        document_id: str | None,
        search_mode: str,
        query: str,
        top_k: int,
    ) -> str:
        ver = cls.get_version(organization_id, document_id)
        norm_query = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
        doc_part = str(document_id) if document_id else "all"
        return f"rag:query:v{ver}:{organization_id}:{doc_part}:{search_mode}:{norm_query}:{top_k}"

    def search_sources(
        self,
        query: str,
        organization_id: str,
        document_id: str | None = None,
        top_k: int = 5,
        candidate_k: int = 20,
        search_mode: str = "hybrid",
        min_score: float = 0.0,
        use_cache: bool = True,
    ) -> list[dict[str, Any]]:
        """Executes search (hybrid, semantic, or lexical) and re-ranking, returning ranked source chunks."""
        if not query or len(query.strip()) < 2:
            return []

        search_mode = search_mode.lower()
        if search_mode not in ("hybrid", "semantic", "lexical"):
            search_mode = "hybrid"

        # Check tenant-isolated cache if enabled
        cache_key = self.compute_cache_key(organization_id, document_id, search_mode, query, top_k)
        if use_cache:
            cached_results = cache.get(cache_key)
            if cached_results is not None:
                logger.debug(f"[RAG] Cache hit for query in org={organization_id}")
                return cached_results

        ranked_results: list[dict[str, Any]] = []

        if search_mode == "lexical":
            ranked_results = self.lexical_search.search(
                query=query,
                organization_id=organization_id,
                document_id=document_id,
                top_k=top_k,
            )
        elif search_mode == "semantic":
            query_vector = None
            try:
                query_vector = self.embedding_provider.embed_text(query)
            except Exception as e:
                logger.error(f"[RAG] Embedding failed during semantic search: {e}")
                # Fallback to lexical search in error scenarios
                ranked_results = self.lexical_search.search(
                    query=query,
                    organization_id=organization_id,
                    document_id=document_id,
                    top_k=top_k,
                )
                return ranked_results

            candidates = self.vector_search.search(
                query_vector=query_vector,
                organization_id=organization_id,
                document_id=document_id,
                top_k=max(candidate_k, top_k),
            )
            ranked_results = self.reranker.rerank(query, candidates, top_k=top_k)
        else:  # hybrid
            query_vector = None
            try:
                query_vector = self.embedding_provider.embed_text(query)
            except Exception as e:
                logger.warning(f"[RAG] Embedding provider failed in hybrid search, falling back to lexical search: {e}")
                query_vector = None

            ranked_results = self.hybrid_search.search(
                query=query,
                query_vector=query_vector,
                organization_id=organization_id,
                document_id=document_id,
                top_k=top_k,
                candidate_k=max(candidate_k, top_k),
                min_score=min_score,
            )

        # Store in cache
        if use_cache and ranked_results:
            cache.set(cache_key, ranked_results, timeout=self.CACHE_TTL_SECONDS)

        return ranked_results

    def query(
        self,
        query: str,
        organization_id: str,
        document_id: str | None = None,
        top_k: int = 5,
        candidate_k: int = 20,
        search_mode: str = "hybrid",
        min_score: float = 0.0,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Executes complete RAG retrieval pipeline, building grounded context, citations, and tracking latency."""
        start_time = time.perf_counter()

        ranked_sources = self.search_sources(
            query=query,
            organization_id=organization_id,
            document_id=document_id,
            top_k=top_k,
            candidate_k=candidate_k,
            search_mode=search_mode,
            min_score=min_score,
            use_cache=use_cache,
        )

        citations = self.citation_builder.build_citations(ranked_sources)
        context = self.context_builder.build_context(ranked_sources)
        prompt = self.context_builder.build_rag_prompt(query, context)
        sources_summary = self.citation_builder.format_sources_summary(citations)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "query": query,
            "organization_id": str(organization_id),
            "document_id": str(document_id) if document_id else None,
            "count": len(ranked_sources),
            "search_mode": search_mode,
            "latency_ms": elapsed_ms,
            "results": ranked_sources,
            "citations": citations,
            "context": context,
            "prompt": prompt,
            "sources_summary": sources_summary,
        }
