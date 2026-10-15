"""Plan-level LLM token budget: accounting (consume_tokens) and enforcement."""

import pytest

from apps.accounts.models import User
from apps.billing.models import PLAN_QUOTAS, UsageMetric, UsageRecord
from apps.billing.services.quota_service import QuotaExceededException, QuotaService
from apps.organizations.models import (
    Organization,
    OrganizationMember,
    PlanChoices,
    RoleChoices,
)


@pytest.fixture
def organization(db):
    owner = User.objects.create_user(email="tokens@org.com", password="Password123!")
    org = Organization.objects.create(name="Token Org", plan=PlanChoices.FREE)
    OrganizationMember.objects.create(
        organization=org, user=owner, role=RoleChoices.OWNER
    )
    return org


@pytest.fixture
def enterprise_org(db):
    owner = User.objects.create_user(
        email="enterprise@org.com", password="Password123!"
    )
    org = Organization.objects.create(name="Unlimited Corp", plan=PlanChoices.ENTERPRISE)
    OrganizationMember.objects.create(
        organization=org, user=owner, role=RoleChoices.OWNER
    )
    return org


class TestTokenConsumption:
    @pytest.mark.django_db
    def test_consume_tokens_increments_usage_record(self, organization):
        recorded = QuotaService.consume_tokens(
            organization, input_tokens=300, output_tokens=200
        )
        assert recorded == 500
        assert (
            QuotaService.get_current_usage(organization, UsageMetric.TOKENS) == 500
        )

    @pytest.mark.django_db
    def test_consume_tokens_accumulates(self, organization):
        QuotaService.consume_tokens(organization, input_tokens=100)
        QuotaService.consume_tokens(organization, input_tokens=50, output_tokens=50)
        assert (
            QuotaService.get_current_usage(organization, UsageMetric.TOKENS) == 200
        )

    @pytest.mark.django_db
    def test_consume_tokens_zero_is_noop(self, organization):
        assert QuotaService.consume_tokens(organization, 0, 0) == 0
        assert not UsageRecord.objects.filter(
            organization=organization, metric=UsageMetric.TOKENS
        ).exists()


class TestTokenBudgetEnforcement:
    @pytest.mark.django_db
    def test_ai_reservation_blocked_when_budget_exhausted(self, organization):
        limit = PLAN_QUOTAS[PlanChoices.FREE]["tokens"]
        QuotaService.consume_tokens(organization, input_tokens=limit)
        with pytest.raises(QuotaExceededException) as exc:
            QuotaService.reserve_quota(
                organization, UsageMetric.AI_GENERATIONS, amount=1
            )
        assert exc.value.metric == UsageMetric.TOKENS
        assert exc.value.limit == limit

    @pytest.mark.django_db
    def test_budget_blocked_before_exhaustion_not_triggered(self, organization):
        QuotaService.consume_tokens(organization, input_tokens=1_000)
        reservation = QuotaService.reserve_quota(
            organization, UsageMetric.AI_GENERATIONS, amount=1
        )
        assert reservation.status == "PENDING"

    @pytest.mark.django_db
    def test_upload_metrics_not_blocked_by_token_budget(self, organization):
        """documents/pages/storage reservations ignore the token budget."""
        limit = PLAN_QUOTAS[PlanChoices.FREE]["tokens"]
        QuotaService.consume_tokens(organization, input_tokens=limit)
        reservation = QuotaService.reserve_quota(
            organization, UsageMetric.DOCUMENTS, amount=1
        )
        assert reservation.status == "PENDING"

    @pytest.mark.django_db
    def test_enterprise_unlimited_never_blocked(self, enterprise_org):
        QuotaService.consume_tokens(enterprise_org, input_tokens=10_000_000)
        reservation = QuotaService.reserve_quota(
            enterprise_org, UsageMetric.AI_GENERATIONS, amount=1
        )
        assert reservation.status == "PENDING"

    @pytest.mark.django_db
    def test_idempotent_replay_survives_budget_exhaustion(self, organization):
        reservation = QuotaService.reserve_quota(
            organization,
            UsageMetric.AI_GENERATIONS,
            amount=1,
            idempotency_key="replay-key",
        )
        limit = PLAN_QUOTAS[PlanChoices.FREE]["tokens"]
        QuotaService.consume_tokens(organization, input_tokens=limit)

        replay = QuotaService.reserve_quota(
            organization,
            UsageMetric.AI_GENERATIONS,
            amount=1,
            idempotency_key="replay-key",
        )
        assert replay.id == reservation.id
