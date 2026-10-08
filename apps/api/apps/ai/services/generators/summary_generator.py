from apps.ai.models import GenerationType

from .base import BaseGenerator


class SummaryGenerator(BaseGenerator):
    """Generates structured, RAG-grounded summaries for documents."""

    generation_type = GenerationType.SUMMARY

    def get_prompts(self, document_title: str, context: str) -> tuple[str, str, str]:
        return self.prompt_service.get_summary_prompt(
            document_title=document_title,
            context=context,
        )
