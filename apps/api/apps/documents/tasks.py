import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="heavy", max_retries=3, default_retry_delay=10)
def process_document_pipeline(self, document_id: str):
    """Executes the full document processing pipeline via ingestion tasks."""
    from apps.ingestion.tasks import process_document

    logger.info(f"[Documents Pipeline] Routing document {document_id} to Ingestion pipeline")
    return process_document(document_id)
