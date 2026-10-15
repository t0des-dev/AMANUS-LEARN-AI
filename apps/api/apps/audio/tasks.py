import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="heavy", max_retries=3, default_retry_delay=15)
def generate_section_audio_task(self, audio_content_id: str, reservation_id: str | None = None):
    """Celery background task for asynchronous Text-to-Speech audio generation.

    Commits the billing quota reservation on success and releases it on
    definitive failure, so quota accounting is always resolved.
    """
    from apps.audio.models import AudioContent
    from apps.billing.services.quota_service import QuotaService

    from .services.audio_service import AudioPipelineService

    logger.info(
        f"[Celery] Starting asynchronous audio generation task for AudioContent {audio_content_id}"
    )
    try:
        service = AudioPipelineService()
        result = service.process_audio_generation(audio_content_id)

        if reservation_id:
            # Actual duration may vary; commit with estimated 1 minute (matches reservation amount)
            QuotaService.commit_quota(reservation_id, actual_amount=1, actual_cost_usd=0.015)

        return {
            "status": "COMPLETED",
            "audio_content_id": str(result.id),
            "duration": result.duration,
            "storage_key": result.storage_key,
        }
    except (ValueError, AudioContent.DoesNotExist) as exc:
        logger.error(f"[Celery] Non-retryable error for AudioContent {audio_content_id}: {exc}")
        if reservation_id:
            QuotaService.release_quota(reservation_id, reason=str(exc))
        raise
    except Exception as exc:
        logger.error(f"[Celery] Audio task failed for {audio_content_id}: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        if reservation_id:
            QuotaService.release_quota(reservation_id, reason=str(exc))
        raise
