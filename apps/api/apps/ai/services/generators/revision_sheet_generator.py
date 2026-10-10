from apps.ai.models import GenerationType

from .base import BaseGenerator


class RevisionSheetGenerator(BaseGenerator):
    """Generates concise exam revision sheets from documents."""

    generation_type = GenerationType.REVISION_SHEET

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
        return self.prompt_service.get_revision_sheet_prompt(
            document_title=document_title,
            context=context,
            language=language,
            level=level,
            focus=focus,
        )
