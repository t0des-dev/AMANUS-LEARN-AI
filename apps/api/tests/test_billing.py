"""Tests for Sprint 14: SaaS Billing, Plans, Quotas, Audit Logs, and System Health."""

import io
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMember, PlanChoices, RoleChoices
from apps.billing.models import (
    PLAN_QUOTAS,
    AuditLog,
    Subscription,
    SubscriptionStatus,
    UsageMetric,
    UsageRecord,
)
from apps.billing.services.quota_service import QuotaService, QuotaExceededException
from apps.billing.services.billing_provider import MockBillingProvider, get_billing_provider
from apps.billing.services.audit_service import AuditLogService
from apps.billing.services.file_security import (
    validate_file_security,
    sanitize_filename,
)
from rest_framework.exceptions import ValidationError


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def owner_user(db):
    return User.objects.create_user(
        email="owner@org.com",
        password="Password123!",
        first_name="Alice",
        last_name="Owner",
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        email="student@org.com",
        password="Password123!",
        first_name="Bob",
        last_name="Student",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="stranger@other.com",
        password="Password123!",
        first_name="Charles",
        last_name="Other",
    )


@pytest.fixture
def organization(db, owner_user, student_user):
    org = Organization.objects.create(name="Acme Academy", plan=PlanChoices.FREE)
    OrganizationMember.objects.create(organization=org, user=owner_user, role=RoleChoices.OWNER)
    OrganizationMember.objects.create(organization=org, user=student_user, role=RoleChoices.STUDENT)
    return org


@pytest.fixture
def other_org(db, other_user):
    org = Organization.objects.create(name="Other Corp", plan=PlanChoices.PRO)
    OrganizationMember.objects.create(organization=org, user=other_user, role=RoleChoices.OWNER)
    return org


# ==============================================================================
# Billing Plans Tests
# ==============================================================================

@pytest.mark.django_db
class TestBillingPlanAPI:
    def test_list_plans_public(self, api_client):
        """GET /api/v1/billing/plan lists all SaaS tiers without auth."""
        url = "/api/v1/billing/plan"
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 4
        plans = [p["plan"] for p in data]
        assert "FREE" in plans
        assert "PRO" in plans
        assert "BUSINESS" in plans
        assert "ENTERPRISE" in plans

        # Verify quota metrics in FREE plan
        free_plan = next(p for p in data if p["plan"] == "FREE")
        assert free_plan["quotas"]["documents"] == 5
        assert free_plan["quotas"]["pages"] == 50
        assert len(free_plan["features"]) > 0

    def test_root_billing_plan_endpoint(self, api_client):
        """GET /billing/plan is accessible directly at root."""
        response = api_client.get("/billing/plan")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 4


# ==============================================================================
# Subscription Tests
# ==============================================================================

@pytest.mark.django_db
class TestBillingSubscriptionAPI:
    def test_get_subscription_authenticated(self, api_client, owner_user, organization):
        """GET /billing/subscription returns current subscription."""
        api_client.force_authenticate(user=owner_user)
        response = api_client.get(f"/billing/subscription?organization_id={organization.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["plan"] == "FREE"
        assert data["status"] == "ACTIVE"
        assert data["is_active"] is True

    def test_change_plan_as_owner(self, api_client, owner_user, organization):
        """Owner can upgrade subscription to PRO."""
        api_client.force_authenticate(user=owner_user)
        payload = {"plan": PlanChoices.PRO, "organization_id": str(organization.id)}
        response = api_client.post("/billing/subscription", payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["plan"] == PlanChoices.PRO

        # Organization plan updated
        organization.refresh_from_db()
        assert organization.plan == PlanChoices.PRO

        # Audit log created
        assert AuditLog.objects.filter(
            organization=organization,
            action="subscription.plan_changed",
        ).exists()

    def test_change_plan_forbidden_for_student(self, api_client, student_user, organization):
        """Non-admin student cannot change subscription plan."""
        api_client.force_authenticate(user=student_user)
        payload = {"plan": PlanChoices.BUSINESS, "organization_id": str(organization.id)}
        response = api_client.post("/billing/subscription", payload, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_subscription_tenant_isolation(self, api_client, other_user, organization):
        """User cannot access subscription of another tenant."""
        api_client.force_authenticate(user=other_user)
        response = api_client.get(f"/billing/subscription?organization_id={organization.id}")
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# Quota Service Tests
# ==============================================================================

@pytest.mark.django_db
class TestQuotaService:
    def test_check_quota_within_limit(self, organization):
        # Free plan: 5 documents
        is_allowed, current, limit = QuotaService.check_quota(organization, UsageMetric.DOCUMENTS, amount=1)
        assert is_allowed is True
        assert current == 0
        assert limit == 5

    def test_increment_and_exceed_quota(self, organization):
        # Increment to limit
        for _ in range(5):
            QuotaService.check_and_increment(organization, UsageMetric.DOCUMENTS, amount=1)

        current = QuotaService.get_current_usage(organization, UsageMetric.DOCUMENTS)
        assert current == 5

        # 6th document must fail
        with pytest.raises(QuotaExceededException) as exc_info:
            QuotaService.check_and_increment(organization, UsageMetric.DOCUMENTS, amount=1)
        assert "Quota dépassé" in str(exc_info.value)

    def test_enterprise_unlimited_quota(self, organization):
        # Upgrade to Enterprise
        sub = QuotaService.get_or_create_subscription(organization)
        sub.plan = PlanChoices.ENTERPRISE
        sub.save()

        # Should never fail even with huge amount
        QuotaService.check_and_increment(organization, UsageMetric.TOKENS, amount=999_999_999)
        is_allowed, current, limit = QuotaService.check_quota(organization, UsageMetric.TOKENS, amount=1_000_000)
        assert is_allowed is True
        assert limit == -1

    def test_usage_summary(self, organization):
        QuotaService.check_and_increment(organization, UsageMetric.AI_GENERATIONS, amount=3)
        summary = QuotaService.get_usage_summary(organization)

        assert "ai_generations" in summary
        assert summary["ai_generations"]["current"] == 3
        assert summary["ai_generations"]["limit"] == 10
        assert summary["ai_generations"]["remaining"] == 7
        assert summary["ai_generations"]["percentage"] == 30.0

    def test_reset_usage(self, organization):
        QuotaService.check_and_increment(organization, UsageMetric.QUIZZES, amount=4)
        assert QuotaService.get_current_usage(organization, UsageMetric.QUIZZES) == 4
        QuotaService.reset_usage(organization, UsageMetric.QUIZZES)
        assert QuotaService.get_current_usage(organization, UsageMetric.QUIZZES) == 0


# ==============================================================================
# Usage API Tests
# ==============================================================================

@pytest.mark.django_db
class TestBillingUsageAPI:
    def test_get_usage_endpoint(self, api_client, owner_user, organization):
        QuotaService.check_and_increment(organization, UsageMetric.DOCUMENTS, amount=2)
        api_client.force_authenticate(user=owner_user)

        response = api_client.get(f"/billing/usage?organization_id={organization.id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["plan"] == "FREE"
        metrics = data["metrics"]
        assert metrics["documents"]["current"] == 2
        assert metrics["documents"]["limit"] == 5
        assert metrics["documents"]["remaining"] == 3


# ==============================================================================
# Audit Log Tests
# ==============================================================================

@pytest.mark.django_db
class TestAuditLogService:
    def test_log_action_and_query(self, owner_user, organization):
        entry = AuditLogService.log(
            action="course.created",
            resource_type="course",
            resource_id="12345",
            actor=owner_user,
            organization=organization,
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0 Test",
            metadata={"title": "Introduction to AI"},
        )
        assert entry.id is not None
        assert entry.action == "course.created"
        assert entry.actor == owner_user

    def test_audit_log_api_access(self, api_client, owner_user, student_user, organization):
        AuditLogService.log(
            action="document.uploaded",
            resource_type="document",
            actor=owner_user,
            organization=organization,
        )

        # Owner has access
        api_client.force_authenticate(user=owner_user)
        res = api_client.get(f"/billing/audit-logs?organization_id={organization.id}")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.json()["results"]) >= 1

        # Student is forbidden
        api_client.force_authenticate(user=student_user)
        res = api_client.get(f"/billing/audit-logs?organization_id={organization.id}")
        assert res.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# File Security Tests
# ==============================================================================

class TestFileSecurity:
    def test_sanitize_filename(self):
        assert sanitize_filename("../../../etc/passwd") == "passwd"
        assert sanitize_filename("safe_file.pdf") == "safe_file.pdf"
        assert sanitize_filename("file\x00withnull.docx") == "filewithnull.docx"

    def test_reject_executable_extensions(self):
        fake_file = SimpleUploadedFile("malware.exe", b"MZ\x90\x00\x03\x00", content_type="application/x-msdownload")
        with pytest.raises(ValidationError) as exc:
            validate_file_security(fake_file)
        assert "strictement interdit" in str(exc.value)

    def test_reject_shell_script(self):
        fake_file = SimpleUploadedFile("script.sh", b"#!/bin/bash\nrm -rf /", content_type="text/x-sh")
        with pytest.raises(ValidationError) as exc:
            validate_file_security(fake_file)
        assert "strictement interdit" in str(exc.value)

    def test_valid_pdf_magic_bytes(self):
        valid_pdf = SimpleUploadedFile("course.pdf", b"%PDF-1.4 sample content", content_type="application/pdf")
        assert validate_file_security(valid_pdf) is True

    def test_invalid_pdf_spoofing(self):
        fake_pdf = SimpleUploadedFile("fake.pdf", b"NOT A PDF HEADER", content_type="application/pdf")
        with pytest.raises(ValidationError) as exc:
            validate_file_security(fake_pdf)
        assert "signature attendue" in str(exc.value)


# ==============================================================================
# System Health Probe Tests
# ==============================================================================

@pytest.mark.django_db
class TestSystemHealthProbe:
    def test_health_probe_status_ok(self, api_client):
        """GET /system/health returns system components status."""
        response = api_client.get("/system/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ("healthy", "degraded")
        assert "components" in data
        assert "database" in data["components"]
        assert data["components"]["database"]["status"] == "ok"
        assert "storage" in data["components"]

    def test_v1_system_health_alias(self, api_client):
        """GET /api/v1/billing/system/health works via v1 route."""
        response = api_client.get("/api/v1/billing/system/health")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["components"]["database"]["status"] == "ok"
