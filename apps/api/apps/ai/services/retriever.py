import logging
from typing import Any

from .citation_builder import CitationBuilder
from .context_builder import ContextBuilder
from .embeddings import EmbeddingProvider, get_embedding_provider
from .reranker import Reranker
from .vector_search import VectorSearchService

logger = logging.getLogger(__name__)


class Retriever:
    """Orchestrates the end-to-end RAG retrieval pipeline:

    Question -> Embedding -> Vector Search -> Metadata Filter -> Top K -> Re-ranking -> Context -> Sources
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider | None = None,
        vector_search: VectorSearchService | None = None,
        reranker: Reranker | None = None,
        context_builder: ContextBuilder | None = None,
        citation_builder: CitationBuilder | None = None,
    ):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.vector_search = vector_search or VectorSearchService()
        self.reranker = reranker or Reranker()
        self.context_builder = context_builder or ContextBuilder()
        self.citation_builder = citation_builder or CitationBuilder()

    def search_sources(
        self,
        query: str,
        organization_id: str,
        document_id: str | None = None,
        top_k: int = 5,
        candidate_k: int = 20,
    ) -> list[dict[str, Any]]:
        """Executes vector search and re-ranking, returning ranked source chunks."""
        if not query or not query.strip():
            return []

        # 1. Question -> Embedding
        query_vector = self.embedding_provider.embed_text(query)

        # 2. Embedding -> Vector Search & Metadata Filter
        candidates = self.vector_search.search(
            query_vector=query_vector,
            organization_id=organization_id,
            document_id=document_id,
            top_k=max(candidate_k, top_k),
        )

        # 3. Top K -> Re-ranking
        ranked = self.reranker.rerank(query, candidates, top_k=top_k)
        return ranked

    def query(
        self,
        query: str,
        organization_id: str,
        document_id: str | None = None,
        top_k: int = 5,
        candidate_k: int = 20,
    ) -> dict[str, Any]:
        """Executes complete RAG retrieval pipeline, building grounded context and citations."""
        ranked_sources = self.search_sources(
            query=query,
            organization_id=organization_id,
            document_id=document_id,
            top_k=top_k,
            candidate_k=candidate_k,
        )

        # 4. Citations & Context Generation
        citations = self.citation_builder.build_citations(ranked_sources)
        context = self.context_builder.build_context(ranked_sources)
        prompt = self.context_builder.build_rag_prompt(query, context)
        sources_summary = self.citation_builder.format_sources_summary(citations)

        return {
            "query": query,
            "organization_id": str(organization_id),
            "document_id": str(document_id) if document_id else None,
            "count": len(ranked_sources),
            "results": ranked_sources,
            "citations": citations,
            "context": context,
            "prompt": prompt,
            "sources_summary": sources_summary,
        }
