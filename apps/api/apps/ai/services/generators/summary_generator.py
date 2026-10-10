from apps.ai.models import GenerationType

from .base import BaseGenerator


class SummaryGenerator(BaseGenerator):
    """Generates structured, RAG-grounded summaries for documents."""

    generation_type = GenerationType.SUMMARY

    def get_prompts(
        self,
        document_title: str,
        context: str,
        language: str = "fr",
        level: str = "BEGINNER",
        focus: str | None = None,
        *args,
        **kwargs,
    ) -> tuple[str, str, str]:
        summary_level = kwargs.get("summary_level", "synthetic")
        return self.prompt_service.get_summary_prompt(
            document_title=document_title,
            context=context,
            language=language,
            level=level,
            focus=focus,
            summary_level=summary_level,
        )
