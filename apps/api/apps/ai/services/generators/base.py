import abc
import json
import logging
from typing import Any

from apps.documents.models import Document
from apps.ingestion.models import DocumentChunk

from ..citation_builder import CitationBuilder
from ..context_builder import ContextBuilder
from ..prompt_service import PromptService
from ..providers.base import AIProvider, AIResponse
from ..retriever import Retriever

logger = logging.getLogger(__name__)


class InsufficientContextError(Exception):
    """Raised when a document has no indexed chunks or insufficient text to generate content."""

    pass


class BaseGenerator(abc.ABC):
    """Base class for RAG-grounded educational AI generators.

    Enforces:
    1. Compulsory RAG source retrieval from DocumentChunks.
    2. Zero hallucination safeguard: refuses generation if context is insufficient.
    3. Traceable citations [1], [2] linked to document chunk metadata.
    4. Structured JSON output production.
    """

    generation_type: str = "UNKNOWN"

    def __init__(
        self,
        prompt_service: PromptService | None = None,
        retriever: Retriever | None = None,
        context_builder: ContextBuilder | None = None,
        citation_builder: CitationBuilder | None = None,
    ):
        self.prompt_service = prompt_service or PromptService()
        self.retriever = retriever or Retriever()
        self.context_builder = context_builder or ContextBuilder()
        self.citation_builder = citation_builder or CitationBuilder()

    @abc.abstractmethod
    def get_prompts(self, document_title: str, context: str) -> tuple[str, str, str]:
        """Returns (system_instruction, user_prompt, prompt_version)."""
        raise NotImplementedError

    def retrieve_context(
        self,
        document: Document,
        focus: str | None = None,
        top_k: int = 5,
    ) -> tuple[str, list[dict[str, Any]], str, list[dict[str, Any]]]:
        """Retrieves and builds RAG context from the document's indexed chunks.

        Returns:
            (context_text, citations, sources_summary, ranked_sources)
        Raises:
            InsufficientContextError: if no chunks exist or content is empty.
        """
        # 1. Safeguard: Check if document has any chunks in database
        chunk_count = DocumentChunk.objects.filter(document=document).count()
        if chunk_count == 0:
            raise InsufficientContextError(
                f"Le document « {document.title} » n'a pas encore été analysé ou découpé en segments (0 chunks). "
                "Veuillez lancer l'ingestion du document avant de générer du contenu."
            )

        # 2. Vector search & Re-ranking via RAG Retriever
        query = (
            focus.strip()
            if focus and focus.strip()
            else f"{document.title} vue d'ensemble concepts clés objectifs pédagogiques"
        )

        ranked_sources = self.retriever.search_sources(
            query=query,
            organization_id=str(document.organization_id),
            document_id=str(document.id),
            top_k=top_k,
        )

        # Fallback to direct sequential chunks if similarity search returned 0 (e.g. no embeddings computed yet)
        if not ranked_sources:
            chunks = (
                DocumentChunk.objects.filter(document=document)
                .select_related("document", "page")
                .order_by("chunk_index")[:top_k]
            )
            ranked_sources = [
                {
                    "chunk_id": str(c.id),
                    "document_id": str(c.document_id),
                    "document_title": c.document.title,
                    "page": c.page.page_number if c.page else None,
                    "chapter": (
                        c.metadata.get("chapter") if isinstance(c.metadata, dict) else None
                    ),
                    "section": (
                        c.metadata.get("section") if isinstance(c.metadata, dict) else None
                    ),
                    "content": c.content,
                    "score": 1.0,
                    "metadata": c.metadata,
                }
                for c in chunks
            ]

        # 3. Safeguard: Ensure at least one non-empty chunk exists
        valid_sources = [s for s in ranked_sources if s.get("content", "").strip()]
        if not valid_sources:
            raise InsufficientContextError(
                f"Contexte insuffisant : le document « {document.title} » ne contient aucun texte exploitable."
            )

        context_text = self.context_builder.build_context(valid_sources)
        if not context_text.strip():
            raise InsufficientContextError(
                f"Contexte insuffisant : le texte extrait du document « {document.title} » est vide."
            )

        citations = self.citation_builder.build_citations(valid_sources)
        sources_summary = self.citation_builder.format_sources_summary(citations)

        return context_text, citations, sources_summary, valid_sources

    def generate(
        self,
        document: Document,
        provider: AIProvider,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
        language: str | None = None,
        level: str | None = None,
    ) -> tuple[dict[str, Any], AIResponse, str]:
        """Executes full generation flow:

        RAG Retrieval -> Prompt Construction -> LLM Generation -> Output Structuring & Citation Enrichment.

        Returns:
            (structured_result, ai_response, prompt_version)
        """
        # Step 1: Retrieve context and citations
        context, citations, sources_summary, _ = self.retrieve_context(
            document=document,
            focus=focus,
            top_k=top_k,
        )

        resolved_lang = (
            language
            or getattr(document, "detected_language", None)
            or getattr(document, "language", None)
            or "fr"
        )
        resolved_level = level or "BEGINNER"

        # Step 2: Build prompts with multilingual and level adaptation
        system_inst, user_prompt, prompt_version = self.get_prompts(
            document_title=document.title,
            context=context,
            language=resolved_lang,
            level=resolved_level,
            focus=focus,
        )

        # Step 3: Invoke AI Provider (Strictly structured JSON)
        ai_response = provider.generate(
            prompt=user_prompt,
            system_instruction=system_inst,
            model=model,
            response_format="json",
        )

        # Step 4: Extract and enrich structured result with citations and metadata
        result_data: dict[str, Any]
        if ai_response.parsed_json and isinstance(ai_response.parsed_json, dict):
            result_data = dict(ai_response.parsed_json)
        else:
            raw_text = (ai_response.content or "").strip()
            # Clean markdown codeblocks ```json ... ``` if present
            if raw_text.startswith("```"):
                import re

                raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
                raw_text = re.sub(r"\s*```$", "", raw_text)
            try:
                result_data = json.loads(raw_text)
                if not isinstance(result_data, dict):
                    result_data = {"raw_content": raw_text}
            except Exception as parse_err:
                logger.warning(
                    "JSON parsing failed for AI response: %s. Storing raw content.",
                    parse_err,
                )
                result_data = {"raw_content": ai_response.content}

        # Inject sources, citations, language and level audit
        result_data["citations"] = citations
        result_data["sources_summary"] = sources_summary
        result_data["document_id"] = str(document.id)
        result_data["document_title"] = document.title
        result_data["language"] = resolved_lang
        result_data["level"] = resolved_level

        return result_data, ai_response, prompt_version
