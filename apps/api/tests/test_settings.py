from django.conf import settings
from django.test import SimpleTestCase


class SettingsConfigurationTests(SimpleTestCase):
    """Verify essential Django settings and installed apps."""

    def test_required_apps_installed(self):
        """Ensure all required internal and third-party apps are present."""
        expected_apps = [
            "rest_framework",
            "corsheaders",
            "drf_spectacular",
            "apps.accounts.apps.AccountsConfig",
            "apps.organizations.apps.OrganizationsConfig",
            "apps.documents.apps.DocumentsConfig",
            "apps.ingestion.apps.IngestionConfig",
            "apps.courses.apps.CoursesConfig",
            "apps.quizzes.apps.QuizzesConfig",
            "apps.learning.apps.LearningConfig",
            "apps.ai.apps.AiConfig",
            "apps.chat.apps.ChatConfig",
            "apps.audio.apps.AudioConfig",
            "apps.slides.apps.SlidesConfig",
            "apps.analytics.apps.AnalyticsConfig",
            "apps.notifications.apps.NotificationsConfig",
        ]
        for app in expected_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_timezone_and_i18n(self):
        """Check timezone is UTC and i18n is enabled."""
        self.assertEqual(settings.TIME_ZONE, "UTC")
        self.assertTrue(settings.USE_I18N)
        self.assertTrue(settings.USE_TZ)

    def test_rest_framework_settings(self):
        """Verify DRF settings are properly configured."""
        self.assertIn("DEFAULT_SCHEMA_CLASS", settings.REST_FRAMEWORK)
        self.assertEqual(
            settings.REST_FRAMEWORK["DEFAULT_SCHEMA_CLASS"],
            "drf_spectacular.openapi.AutoSchema",
        )
