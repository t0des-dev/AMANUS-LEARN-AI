from apps.ai.models import GenerationType

from .base import BaseGenerator


class ObjectiveGenerator(BaseGenerator):
    """Generates educational learning objectives from documents."""

    generation_type = GenerationType.OBJECTIVES

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
        return self.prompt_service.get_objectives_prompt(
            document_title=document_title,
            context=context,
            language=language,
            level=level,
            focus=focus,
        )
