"""Celery tasks for document processing and ingestion."""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="document.process_document")
def process_document_task(document_id: str):
    """Executes text extraction, structuring and chunking for document."""
    from apps.ingestion.tasks import process_document

    logger.info("Processing document task initiated for ID: %s", document_id)
    return process_document(document_id)
