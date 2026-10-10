from apps.ai.models import GenerationType

from .base import BaseGenerator


class KeyPointGenerator(BaseGenerator):
    """Generates structured, RAG-grounded key points and core concepts for documents."""

    generation_type = GenerationType.KEY_POINTS

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
        return self.prompt_service.get_key_points_prompt(
            document_title=document_title,
            context=context,
            language=language,
            level=level,
            focus=focus,
        )
