import logging
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="default", max_retries=3, default_retry_delay=5)
def send_notification_task(
    self,
    recipient_id: str,
    title: str,
    message: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Lightweight Celery task for delivering transactional notifications."""
    logger.info(
        f"[Notifications] Dispatching notification to recipient {recipient_id}: {title}"
    )
    return {
        "status": "DELIVERED",
        "recipient_id": recipient_id,
        "title": title,
        "payload": payload or {},
    }


@shared_task(bind=True, queue="default", max_retries=2, default_retry_delay=10)
def send_system_alert_task(
    self,
    alert_level: str,
    message: str,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Lightweight task for emitting administrative system alerts."""
    logger.warning(f"[Notifications Alert] [{alert_level.upper()}] {message}")
    return {
        "status": "SENT",
        "alert_level": alert_level,
        "message": message,
        "context": context or {},
    }
