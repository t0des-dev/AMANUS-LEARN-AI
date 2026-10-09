import json
import logging
from typing import Any, Generator

from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.ai.services import (
    CitationBuilder,
    ContextBuilder,
    Retriever,
    get_ai_provider,
)
from apps.documents.models import Document

from ..models import ChatMessage, ChatSession, MessageRole
from .pedagogical_commands import detect_pedagogical_command, get_command_instruction

logger = logging.getLogger(__name__)


class AITutorService:
    """Orchestrates end-to-end pedagogical AI Tutor pipeline:

    Question -> History/Context -> RAG Retrieval -> Grounded Prompt -> LLM -> Streaming -> Sources
    """

    def __init__(
        self,
        retriever: Retriever | None = None,
        citation_builder: CitationBuilder | None = None,
        context_builder: ContextBuilder | None = None,
        ai_provider=None,
    ):
        self.retriever = retriever or Retriever()
        self.citation_builder = citation_builder or CitationBuilder()
        self.context_builder = context_builder or ContextBuilder()
        self.ai_provider = ai_provider or get_ai_provider()

    def validate_document_access(
        self, session: ChatSession, document_id: str | None
    ) -> str | None:
        """Validates that target document belongs to the session's organization."""
        target_doc_id = document_id or (
            str(session.document_id) if session.document_id else None
        )
        if not target_doc_id:
            return None

        doc_exists = Document.objects.filter(
            id=target_doc_id,
            organization=session.organization,
        ).exists()

        if not doc_exists:
            raise PermissionDenied(
                "Le document demandé n'existe pas ou n'est pas accessible pour votre organisation."
            )

        return target_doc_id

    def build_conversation_history(
        self, session: ChatSession, limit: int = 6
    ) -> str:
        """Assembles recent conversation history for memory and context continuity."""
        recent_messages = list(
            session.messages.order_by("-created_at")[:limit]
        )
        recent_messages.reverse()

        if not recent_messages:
            return ""

        lines = []
        for msg in recent_messages:
            speaker = "Étudiant" if msg.role == MessageRole.USER else "Tuteur IA"
            lines.append(f"{speaker} : {msg.content}")

        return "\n".join(lines)

    def prepare_rag_context(
        self,
        session: ChatSession,
        query: str,
        document_id: str | None = None,
        top_k: int = 5,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
        """Executes retrieval against accessible documents in the organization.

        Returns:
            (ranked_sources, citations, formatted_context)
        """
        target_doc_id = self.validate_document_access(session, document_id)

        ranked_sources = self.retriever.search_sources(
            query=query,
            organization_id=str(session.organization_id),
            document_id=target_doc_id,
            top_k=top_k,
        )

        # If no specific chunk matched a very concise pedagogical command,
        # fallback search enriched with the document title for grounding
        if not ranked_sources and target_doc_id:
            doc = Document.objects.filter(id=target_doc_id).first()
            if doc and doc.title:
                enriched_query = f"{doc.title} {query}".strip()
                ranked_sources = self.retriever.search_sources(
                    query=enriched_query,
                    organization_id=str(session.organization_id),
                    document_id=target_doc_id,
                    top_k=top_k,
                )

        citations = self.citation_builder.build_citations(ranked_sources)
        context = self.context_builder.build_context(ranked_sources)

        return ranked_sources, citations, context

    def assemble_prompt_payload(
        self,
        query: str,
        command_code: str | None,
        context: str,
        history: str,
    ) -> tuple[str, str]:
        """Constructs system instruction and grounded prompt payload."""
        command_instruction = get_command_instruction(command_code)

        system_instruction = (
            "Tu es l'assistant pédagogique conversationnel officiel de la plateforme Amanus Learn AI.\n"
            f"{command_instruction}\n\n"
            "RÈGLE D'OR DE RIGUEUR ET ANTI-HALLUCINATION :\n"
            "1. Base TOUTES tes explications EXCLUSIVEMENT sur les sources documentaires fournies.\n"
            "2. Cite systématiquement tes sources sous la forme [1], [2], etc., directement dans le texte.\n"
            "3. N'invente aucun fait, chiffre ou concept absent des sources.\n"
            "4. Si l'information n'est pas présente dans les sources, réponds avec courtoisie et précision : "
            "« Cette information n'est pas présente dans les documents disponibles. »"
        )

        prompt_parts = []
        if history:
            prompt_parts.append(f"--- HISTORIQUE DU DIALOGUE ---\n{history}\n")

        if context:
            prompt_parts.append(f"--- SOURCES DOCUMENTAIRES ACCESSIBLES ---\n{context}\n")
        else:
            prompt_parts.append(
                "--- SOURCES DOCUMENTAIRES ---\nAucun document pertinent trouvé dans l'organisation.\n"
            )

        prompt_parts.append(f"--- QUESTION DE L'ÉTUDIANT ---\n{query}")

        prompt = "\n".join(prompt_parts)
        return system_instruction, prompt

    def update_session_title_if_needed(self, session: ChatSession, query: str):
        """Auto-updates the default session title based on the first question."""
        default_titles = [
            "Nouvelle session",
            "Nouvelle session pédagogique",
            "Nouvelle conversation",
        ]
        if session.title in default_titles:
            truncated = query.strip().split("\n")[0][:45]
            if truncated:
                session.title = truncated
                session.save(update_fields=["title", "updated_at"])

    def process_message_sync(
        self,
        session: ChatSession,
        user_content: str,
        explicit_command: str | None = None,
        document_id: str | None = None,
    ) -> tuple[ChatMessage, ChatMessage]:
        """Synchronous generation flow returning saved user and assistant ChatMessages."""
        # 1. Déterminer le contexte
        command_code, clean_query = detect_pedagogical_command(
            user_content, explicit_command=explicit_command
        )

        with transaction.atomic():
            user_msg = ChatMessage.objects.create(
                session=session,
                role=MessageRole.USER,
                content=user_content,
                command=command_code,
            )
            self.update_session_title_if_needed(session, clean_query)

        history = self.build_conversation_history(session, limit=6)

        # 2. Effectuer retrieval
        ranked_sources, citations, context = self.prepare_rag_context(
            session=session,
            query=clean_query,
            document_id=document_id,
        )

        # 3. Construire le contexte et prompt
        system_instruction, prompt = self.assemble_prompt_payload(
            query=clean_query,
            command_code=command_code,
            context=context,
            history=history,
        )

        # 4. Interroger AIProvider
        if not context:
            assistant_content = (
                "Cette information n'est pas présente dans les documents disponibles."
            )
            input_tokens = len(prompt.split())
            output_tokens = len(assistant_content.split())
        else:
            response = self.ai_provider.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                temperature=0.2,
                max_tokens=2500,
            )
            assistant_content = response.content
            input_tokens = response.input_tokens
            output_tokens = response.output_tokens

        # 5 & 6. Enregistrer et retourner réponse + sources
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            command=command_code,
            sources=citations,
            tokens_used=input_tokens + output_tokens,
            metadata={
                "provider": getattr(self.ai_provider, "name", "unknown"),
                "clean_query": clean_query,
                "sources_count": len(citations),
            },
        )

        session.save(update_fields=["updated_at"])
        return user_msg, assistant_msg

    def process_message_stream(
        self,
        session: ChatSession,
        user_content: str,
        explicit_command: str | None = None,
        document_id: str | None = None,
    ) -> Generator[str, None, None]:
        """Streaming SSE generation flow returning Server-Sent Events."""
        # 1. Déterminer le contexte
        command_code, clean_query = detect_pedagogical_command(
            user_content, explicit_command=explicit_command
        )

        with transaction.atomic():
            user_msg = ChatMessage.objects.create(
                session=session,
                role=MessageRole.USER,
                content=user_content,
                command=command_code,
            )
            self.update_session_title_if_needed(session, clean_query)

        # Send initial user_message event so client knows user message is registered
        yield f"data: {json.dumps({'type': 'start', 'user_message_id': str(user_msg.id), 'command': command_code})}\n\n"

        history = self.build_conversation_history(session, limit=6)

        # 2. Effectuer retrieval
        ranked_sources, citations, context = self.prepare_rag_context(
            session=session,
            query=clean_query,
            document_id=document_id,
        )

        # 3. Construire le contexte et prompt
        system_instruction, prompt = self.assemble_prompt_payload(
            query=clean_query,
            command_code=command_code,
            context=context,
            history=history,
        )

        full_content_chunks: list[str] = []

        if not context:
            fallback = (
                "Cette information n'est pas présente dans les documents disponibles."
            )
            full_content_chunks.append(fallback)
            yield f"data: {json.dumps({'type': 'token', 'content': fallback})}\n\n"
        else:
            try:
                for token in self.ai_provider.stream_generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=0.2,
                    max_tokens=2500,
                ):
                    full_content_chunks.append(token)
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            except Exception as exc:
                logger.error(f"[AITutorService] Streaming error: {exc}", exc_info=True)
                err_text = " Une erreur est survenue lors de la génération."
                full_content_chunks.append(err_text)
                yield f"data: {json.dumps({'type': 'token', 'content': err_text})}\n\n"

        full_content = "".join(full_content_chunks)

        # 5 & 6. Enregistrer assistant message et retourner sources
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=MessageRole.ASSISTANT,
            content=full_content,
            command=command_code,
            sources=citations,
            tokens_used=len(prompt.split()) + len(full_content.split()),
            metadata={
                "provider": getattr(self.ai_provider, "name", "unknown"),
                "clean_query": clean_query,
                "sources_count": len(citations),
            },
        )

        session.save(update_fields=["updated_at"])

        # Final done event with sources and metadata
        done_payload = {
            "type": "done",
            "message_id": str(assistant_msg.id),
            "command": command_code,
            "sources": citations,
            "content": full_content,
        }
        yield f"data: {json.dumps(done_payload)}\n\n"
