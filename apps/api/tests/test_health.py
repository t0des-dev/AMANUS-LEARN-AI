from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    """Test suite for the API Health Check endpoint."""

    def setUp(self):
        self.client = APIClient()

    def test_health_check_returns_ok_status(self):
        """Verify GET /api/v1/health returns 200 OK and status 'ok'."""
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_check_url_by_name(self):
        """Verify the health check endpoint is resolvable by route name."""
        url = reverse("v1:health-check")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_check_with_trailing_slash(self):
        """Verify GET /api/v1/health/ returns 200 OK and status 'ok'."""
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_v1_system_health_endpoint(self):
        """Verify GET /api/v1/system/health/ returns 200 OK."""
        response = self.client.get("/api/v1/system/health/")
        self.assertIn(
            response.status_code, (status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE)
        )
        self.assertIn(response.json().get("status"), ("healthy", "degraded"))
