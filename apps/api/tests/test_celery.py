from django.test import SimpleTestCase

from config.celery import app as celery_app


class CeleryConfigurationTests(SimpleTestCase):
    """Test Celery setup and tasks configuration."""

    def test_celery_app_initialization(self):
        """Verify Celery app name and basic properties."""
        self.assertEqual(celery_app.main, "amanus_learn_ai")

    def test_celery_debug_task_registered(self):
        """Verify the Celery debug task is registered."""
        self.assertIn("config.celery.debug_task", celery_app.tasks)
