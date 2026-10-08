from apps.ai.models import GenerationType

from .base import BaseGenerator


class ObjectiveGenerator(BaseGenerator):
    """Generates structured, pedagogical objectives based on Bloom taxonomy."""

    generation_type = GenerationType.OBJECTIVES

    def get_prompts(self, document_title: str, context: str) -> tuple[str, str, str]:
        return self.prompt_service.get_objectives_prompt(
            document_title=document_title,
            context=context,
        )
