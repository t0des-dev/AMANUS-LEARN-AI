import pytest
from django.conf import settings

from apps.audio.tasks import generate_section_audio_task
from apps.documents.tasks import process_document_pipeline
from apps.ingestion.tasks import process_document
from apps.notifications.tasks import send_notification_task, send_system_alert_task
from apps.slides.tasks import export_presentation_task
from config.celery import app as celery_app


@pytest.mark.django_db
class TestCeleryQueueArchitecture:
    """Validate Phase 15.4 Celery queue segregation between default and heavy."""

    def test_celery_queues_defined_in_settings(self):
        """Ensure default and heavy queues are configured."""
        queues = settings.CELERY_QUEUES
        assert "default" in queues
        assert "heavy" in queues
        assert settings.CELERY_TASK_DEFAULT_QUEUE == "default"

    def test_heavy_task_annotations_and_queue_attributes(self):
        """Heavy tasks must have queue='heavy' explicitly assigned."""
        assert process_document_pipeline.queue == "heavy"
        assert process_document.queue == "heavy"
        assert generate_section_audio_task.queue == "heavy"
        assert export_presentation_task.queue == "heavy"

    def test_default_task_annotations_and_queue_attributes(self):
        """Lightweight / notification tasks must have queue='default'."""
        assert send_notification_task.queue == "default"
        assert send_system_alert_task.queue == "default"

    def test_router_routes_heavy_tasks_to_heavy_queue(self):
        """Celery AMQP router routes heavy tasks to 'heavy' queue."""
        router = celery_app.amqp.router
        heavy_tasks = [
            "apps.documents.tasks.process_document_pipeline",
            "apps.ingestion.tasks.process_document",
            "apps.audio.tasks.generate_section_audio_task",
            "apps.slides.tasks.export_presentation_task",
        ]
        for task_name in heavy_tasks:
            route = router.route(options={}, name=task_name)
            queue_name = route.get("queue")
            if hasattr(queue_name, "name"):
                queue_name = queue_name.name
            assert queue_name == "heavy", f"Expected task {task_name} to route to 'heavy', got {queue_name}"

    def test_router_routes_lightweight_tasks_to_default_queue(self):
        """Celery AMQP router routes notifications to 'default' queue."""
        router = celery_app.amqp.router
        light_tasks = [
            "apps.notifications.tasks.send_notification_task",
            "apps.notifications.tasks.send_system_alert_task",
            "config.celery.debug_task",
        ]
        for task_name in light_tasks:
            route = router.route(options={}, name=task_name)
            queue_name = route.get("queue")
            if hasattr(queue_name, "name"):
                queue_name = queue_name.name
            assert queue_name == "default", f"Expected task {task_name} to route to 'default', got {queue_name}"
