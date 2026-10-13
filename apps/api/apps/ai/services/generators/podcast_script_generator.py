from apps.ai.models import GenerationType

from .base import BaseGenerator


class PodcastScriptGenerator(BaseGenerator):
    """Generates structured, RAG-grounded dual-host pedagogical podcast dialogues (NotebookLM style)."""

    generation_type = GenerationType.PODCAST_SCRIPT

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
        return self.prompt_service.get_podcast_dialogue_prompt(
            document_title=document_title,
            context=context,
            language=language,
            level=level,
            focus=focus,
        )
