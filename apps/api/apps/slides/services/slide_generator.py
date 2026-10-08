import logging
from typing import Any

from django.db import transaction

from apps.courses.models import Course
from apps.slides.models import Presentation, PresentationSlide, PresentationStatus, PresentationTheme
from apps.slides.services.slide_planner import SlidePlanner

logger = logging.getLogger(__name__)


class SlideGenerator:
    """Generates a complete pedagogical Presentation from a Course.

    Coordinates SlidePlanner to compute slide blueprints and persists
    Presentation and PresentationSlide instances in the database.
    """

    def __init__(self, planner: SlidePlanner | None = None) -> None:
        self.planner = planner or SlidePlanner()

    def generate_presentation(
        self,
        course: Course,
        title: str | None = None,
        theme: str = PresentationTheme.MODERN_DARK,
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
                blueprints = self.planner.plan_presentation(course, title=presentation_title)

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
