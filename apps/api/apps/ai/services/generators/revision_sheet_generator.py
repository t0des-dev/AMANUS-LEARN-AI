from apps.ai.models import GenerationType

from .base import BaseGenerator


class RevisionSheetGenerator(BaseGenerator):
    """Generates structured revision sheets (fiches de révision) for documents."""

    generation_type = GenerationType.REVISION_SHEET

    def get_prompts(self, document_title: str, context: str) -> tuple[str, str, str]:
        return self.prompt_service.get_revision_sheet_prompt(
            document_title=document_title,
            context=context,
        )
