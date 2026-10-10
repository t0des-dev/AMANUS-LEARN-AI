from apps.ai.models import GenerationType

from .base import BaseGenerator


class LessonGenerator(BaseGenerator):
    """Generates structured, pedagogical courses and lessons from documents."""

    generation_type = GenerationType.LESSON

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
        return self.prompt_service.get_lesson_prompt(
            document_title=document_title,
            context=context,
            language=language,
            level=level,
            focus=focus,
        )
