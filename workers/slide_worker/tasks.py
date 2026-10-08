"""Celery tasks for slide generation (Sprint Slides)."""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name="slides.generate_deck")
def generate_deck_task(summary_id: str, template: str = "standard"):
    """
    Placeholder task for slide and presentation generation.
    Full implementation scheduled in Slides sprint.
    """
    logger.info("Generating slide deck for summary: %s with template: %s", summary_id, template)
    return {"status": "pending_sprint_implementation"}
