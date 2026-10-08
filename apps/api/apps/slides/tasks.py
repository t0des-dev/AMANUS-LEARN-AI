import logging

from celery import shared_task

from apps.slides.models import Presentation, PresentationStatus
from apps.slides.services.pptx_exporter import PPTXExporter

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="heavy", max_retries=3, default_retry_delay=10)
def export_presentation_task(self, presentation_id: str):
    """Celery background task for asynchronous PPTX export."""
    logger.info("[Celery] Starting asynchronous PPTX export task for Presentation %s", presentation_id)
    try:
        presentation = Presentation.objects.get(id=presentation_id)
        exporter = PPTXExporter()
        storage_key = exporter.export_and_save(presentation)
        return {
            "status": "READY",
            "presentation_id": str(presentation.id),
            "storage_key": storage_key,
            "export_url": presentation.get_export_url(),
        }
    except Presentation.DoesNotExist:
        logger.error("[Celery] Presentation %s not found for export task", presentation_id)
        return {"status": "FAILED", "error": "Presentation not found"}
    except Exception as exc:
        logger.error("[Celery] Presentation export failed for %s: %s", presentation_id, exc)
        try:
            pres = Presentation.objects.get(id=presentation_id)
            pres.status = PresentationStatus.FAILED
            pres.save(update_fields=["status", "updated_at"])
        except Exception:
            pass
        raise self.retry(exc=exc)
