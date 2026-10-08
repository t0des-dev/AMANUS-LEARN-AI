"""Celery tasks for AI embedding and text generation (Sprint AI & RAG)."""

from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(name="ai.generate_embeddings")
def generate_embeddings_task(chunk_ids: list):
    """
    Placeholder task for vector embedding generation.
    Full implementation scheduled in AI Engine sprint.
    """
    logger.info("Generating embeddings for %d chunks", len(chunk_ids))
    return {"status": "pending_sprint_implementation", "count": len(chunk_ids)}
