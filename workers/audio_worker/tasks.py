"""Celery tasks for TTS audio generation (Sprint Audio)."""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name="audio.synthesize_speech")
def synthesize_speech_task(text_script: str, voice_profile: str = "default"):
    """
    Placeholder task for audio course speech synthesis.
    Full implementation scheduled in Audio sprint.
    """
    logger.info("Synthesizing audio course with profile: %s", voice_profile)
    return {"status": "pending_sprint_implementation"}
