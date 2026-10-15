import logging

from django.db import transaction

from apps.ai.services.generation_service import GenerationService
from apps.ai.services.generators.slide_generator import SlideDeckGenerator
from apps.courses.models import Course
from apps.slides.models import (
    Presentation,
    PresentationSlide,
    PresentationStatus,
    PresentationTheme,
)
from apps.slides.services.slide_planner import SlidePlanner
from apps.slides.services.validator import PresentationValidator

logger = logging.getLogger(__name__)


class SlideGenerator:
    """Generates a complete pedagogical Presentation from a Course.

    When the course is backed by an indexed document, slides are produced by the
    RAG-grounded ``SlideDeckGenerator`` (with a full AIGeneration audit trail and
    token billing). Otherwise, or if the AI path fails, it degrades gracefully to
    the deterministic ``SlidePlanner`` templates.
    """

    def __init__(
        self,
        planner: SlidePlanner | None = None,
        generation_service: GenerationService | None = None,
    ) -> None:
        self.planner = planner or SlidePlanner()
        self.generation_service = generation_service or GenerationService()

    def generate_presentation(
        self,
        course: Course,
        title: str | None = None,
        theme: str = PresentationTheme.MODERN_DARK,
        language: str | None = None,
        level: str | None = None,
        focus: str | None = None,
        user=None,
    ) -> Presentation:
        """Plans and generates a new Presentation with all slides."""
        presentation_title = (title or course.title).strip()

        with transaction.atomic():
            presentation = Presentation.objects.create(
                course=course,
                title=presentation_title,
                theme=theme,
                status=PresentationStatus.GENERATING,
            )

            try:
                blueprints = self._plan_blueprints(
                    course=course,
                    title=presentation_title,
                    language=language,
                    level=level,
                    focus=focus,
                    user=user,
                )

                slide_instances = [
                    PresentationSlide(
                        presentation=presentation,
                        slide_number=bp["slide_number"],
                        title=bp["title"],
                        content=bp.get("content", ""),
                        speaker_notes=bp.get("speaker_notes", ""),
                        image_prompt=bp.get("image_prompt", ""),
                        image_url=bp.get("image_url", ""),
                    )
                    for bp in blueprints
                ]

                PresentationSlide.objects.bulk_create(slide_instances)

                presentation.status = PresentationStatus.READY
                presentation.save(update_fields=["status", "updated_at"])

                logger.info(
                    "Generated presentation %s with %d slides for course %s",
                    presentation.id,
                    len(slide_instances),
                    course.id,
                )
                return presentation

            except Exception as exc:
                presentation.status = PresentationStatus.FAILED
                presentation.save(update_fields=["status", "updated_at"])
                logger.error(
                    "Failed generating slides for presentation %s: %s",
                    presentation.id,
                    exc,
                    exc_info=True,
                )
                raise

    def _plan_blueprints(
        self,
        course: Course,
        title: str,
        language: str | None,
        level: str | None,
        focus: str | None,
        user=None,
    ) -> list[dict]:
        """Returns AI-generated blueprints when possible, else heuristic ones."""
        document = course.document
        if document is not None and document.chunks.exists():
            try:
                generation = self.generation_service.generate_slides(
                    document=document,
                    user=user,
                    language=language or course.language,
                    level=level or course.level,
                    focus=focus,
                    top_k=8,
                )
                blueprints = self._validate_blueprints(
                    SlideDeckGenerator.to_blueprints(
                        generation.result, fallback_title=title
                    )
                )
                if blueprints:
                    logger.info(
                        "Slide deck for course %s generated via AI (%s), %d slides",
                        course.id,
                        generation.provider,
                        len(blueprints),
                    )
                    return blueprints
                logger.warning(
                    "AI slide payload for course %s was empty, using heuristic planner",
                    course.id,
                )
            except Exception as exc:
                logger.warning(
                    "AI slide generation failed for course %s, "
                    "falling back to heuristic planner: %s",
                    course.id,
                    exc,
                    exc_info=True,
                )

        return self.planner.plan_presentation(
            course,
            title=title,
            language=language,
            level=level,
            focus=focus,
        )

    @staticmethod
    def _validate_blueprints(blueprints: list[dict]) -> list[dict]:
        """Applies the presentation density caps to AI-produced blueprints."""
        validated: list[dict] = []
        for bp in blueprints:
            slide = PresentationValidator.validate_slide_content(
                title=bp["title"],
                content=bp.get("content", ""),
                slide_number=bp["slide_number"],
            )
            validated.append(
                {
                    **bp,
                    "title": slide["title"],
                    "content": slide["content"],
                }
            )
        return validated
