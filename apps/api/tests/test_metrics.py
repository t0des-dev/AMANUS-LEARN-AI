"""Tests for the Prometheus /metrics endpoint and metrics instrumentation."""

import pytest
from prometheus_client import REGISTRY

from apps.accounts.models import User
from apps.billing.models import UsageMetric
from apps.billing.services.quota_service import QuotaExceededException, QuotaService
from apps.organizations.models import (
    Organization,
    OrganizationMember,
    PlanChoices,
    RoleChoices,
)
from config.metrics import timed_ai_call


def _value(name: str, **labels) -> float:
    return REGISTRY.get_sample_value(name, labels) or 0.0


@pytest.fixture
def organization(db):
    owner = User.objects.create_user(
        email="metrics@org.com",
        password="Password123!",
    )
    org = Organization.objects.create(name="Metrics Org", plan=PlanChoices.FREE)
    OrganizationMember.objects.create(
        organization=org, user=owner, role=RoleChoices.OWNER
    )
    return org


class TestMetricsEndpoint:
    def test_metrics_exposed_without_authentication(self, client):
        """GET /metrics returns 200 in Prometheus text format without auth."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response["Content-Type"].startswith("text/plain")
        body = response.content.decode()
        assert "amanus_ai_request_duration_seconds" in body
        assert "amanus_quota_reservations_total" in body
        assert "amanus_quota_commits_total" in body

    def test_metrics_carry_no_tenant_identifiers(self, client, organization):
        """Scraped metrics never expose organization or user identifiers."""
        QuotaService.reserve_quota(organization, UsageMetric.DOCUMENTS, amount=1)
        body = client.get("/metrics").content.decode()
        assert organization.name not in body
        assert str(organization.id) not in body


class TestTimedAICall:
    def test_successful_call_recorded(self):
        labels = dict(provider="unit-test", operation="unit", status="success")
        before = _value("amanus_ai_request_duration_seconds_count", **labels)
        with timed_ai_call(provider="unit-test", operation="unit"):
            pass
        assert _value("amanus_ai_request_duration_seconds_count", **labels) == before + 1

    def test_failed_call_recorded_with_error_status(self):
        labels = dict(provider="unit-test", operation="unit", status="error")
        before = _value("amanus_ai_request_duration_seconds_count", **labels)
        with pytest.raises(ValueError, match="boom"):
            with timed_ai_call(provider="unit-test", operation="unit"):
                raise ValueError("boom")
        assert _value("amanus_ai_request_duration_seconds_count", **labels) == before + 1


class TestQuotaMetrics:
    @pytest.mark.django_db
    def test_allowed_reservation_counted(self, organization):
        labels = dict(metric=UsageMetric.DOCUMENTS, outcome="allowed")
        before = _value("amanus_quota_reservations_total", **labels)
        QuotaService.reserve_quota(organization, UsageMetric.DOCUMENTS, amount=1)
        assert _value("amanus_quota_reservations_total", **labels) == before + 1

    @pytest.mark.django_db
    def test_rejected_reservation_counted(self, organization):
        labels = dict(metric=UsageMetric.DOCUMENTS, outcome="rejected")
        before = _value("amanus_quota_reservations_total", **labels)
        with pytest.raises(QuotaExceededException):
            QuotaService.reserve_quota(
                organization, UsageMetric.DOCUMENTS, amount=10_000_000
            )
        assert _value("amanus_quota_reservations_total", **labels) == before + 1

    @pytest.mark.django_db
    def test_commit_and_release_counted(self, organization):
        committed = dict(metric=UsageMetric.DOCUMENTS, outcome="committed")
        released = dict(metric=UsageMetric.DOCUMENTS, outcome="released")

        res_ok = QuotaService.reserve_quota(
            organization, UsageMetric.DOCUMENTS, amount=1, idempotency_key="m-ok"
        )
        before_commit = _value("amanus_quota_commits_total", **committed)
        QuotaService.commit_quota(res_ok)
        assert _value("amanus_quota_commits_total", **committed) == before_commit + 1

        res_fail = QuotaService.reserve_quota(
            organization, UsageMetric.DOCUMENTS, amount=1, idempotency_key="m-fail"
        )
        before_release = _value("amanus_quota_commits_total", **released)
        QuotaService.release_quota(res_fail, reason="failed")
        assert _value("amanus_quota_commits_total", **released) == before_release + 1
