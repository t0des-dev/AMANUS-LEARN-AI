import logging
from typing import Any

from apps.documents.models import Document

from ..models import AIGeneration
from .generation_service import GenerationService
from .generators.base import InsufficientContextError

logger = logging.getLogger(__name__)


class AIService:
    """High-level AI facade for Amanus Learn AI.

    Views and external tasks must ALWAYS interact through this service and NEVER
    call AI providers directly.
    """

    def __init__(self, generation_service: GenerationService | None = None):
        self.generation_service = generation_service or GenerationService()

    def generate_summary(
        self,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
    ) -> AIGeneration:
        """Generates a structured educational summary from document RAG chunks."""
        return self.generation_service.generate_summary(
            document=document,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
        )

    def generate_course(
        self,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
    ) -> AIGeneration:
        """Generates a comprehensive pedagogical course / lesson from document RAG chunks."""
        return self.generation_service.generate_lesson(
            document=document,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
        )

    def generate_objectives(
        self,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
    ) -> AIGeneration:
        """Generates learning objectives based on educational taxonomies."""
        return self.generation_service.generate_objectives(
            document=document,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
        )

    def generate_key_points(
        self,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
    ) -> AIGeneration:
        """Extracts essential notions and key points from document RAG chunks."""
        return self.generation_service.generate_key_points(
            document=document,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
        )

    def generate_revision_sheet(
        self,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
    ) -> AIGeneration:
        """Generates a concise exam revision sheet from document RAG chunks."""
        return self.generation_service.generate_revision_sheet(
            document=document,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
        )


__all__ = ["AIService", "InsufficientContextError"]
