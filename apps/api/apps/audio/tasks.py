import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="heavy", max_retries=3, default_retry_delay=15)
def generate_section_audio_task(self, audio_content_id: str):
    """Celery background task for asynchronous Text-to-Speech audio generation."""
    from apps.audio.models import AudioContent

    from .services.audio_service import AudioPipelineService

    logger.info(
        f"[Celery] Starting asynchronous audio generation task for AudioContent {audio_content_id}"
    )
    try:
        service = AudioPipelineService()
        result = service.process_audio_generation(audio_content_id)
        return {
            "status": "COMPLETED",
            "audio_content_id": str(result.id),
            "duration": result.duration,
            "storage_key": result.storage_key,
        }
    except (ValueError, AudioContent.DoesNotExist) as exc:
        logger.error(f"[Celery] Non-retryable error for AudioContent {audio_content_id}: {exc}")
        raise
    except Exception as exc:
        logger.error(f"[Celery] Audio task failed for {audio_content_id}: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        raise
