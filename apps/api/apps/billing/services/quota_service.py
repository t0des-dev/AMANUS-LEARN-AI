"""Quota Management Service.

Enforces resource limits, tracks usage records, and prevents resource exhaustion
across organizations according to their active subscription plan.
"""

import logging
from typing import Any

from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from apps.billing.models import (
    PLAN_QUOTAS,
    PlanChoices,
    Subscription,
    SubscriptionStatus,
    UsageMetric,
    UsageRecord,
)

logger = logging.getLogger(__name__)


class QuotaExceededException(PermissionDenied):
    """Raised when an organization attempts to exceed its plan quota limits."""

    def __init__(self, metric: str, current: int, limit: int, requested: int = 1):
        self.metric = metric
        self.current = current
        self.limit = limit
        self.requested = requested
        detail = (
            f"Quota dépassé pour '{metric}'. Limite du plan : {limit}, "
            f"consommation actuelle : {current}, demandé : {requested}. "
            f"Veuillez mettre à niveau votre abonnement."
        )
        super().__init__(detail=detail, code="quota_exceeded")


class QuotaService:
    """Service to inspect, increment, and summarize quota consumption per organization."""

    @classmethod
    def get_or_create_subscription(cls, organization) -> Subscription:
        """Retrieve existing subscription or provision a default FREE subscription."""
        subscription = getattr(organization, "subscription", None)
        if subscription is None:
            # Check DB directly in case of un-cached relation
            subscription = Subscription.objects.filter(organization=organization).first()
            if subscription is None:
                # Use organization.plan if set, else FREE
                plan = getattr(organization, "plan", PlanChoices.FREE)
                if plan not in PlanChoices.values:
                    plan = PlanChoices.FREE
                subscription = Subscription.objects.create(
                    organization=organization,
                    plan=plan,
                    status=SubscriptionStatus.ACTIVE,
                    started_at=timezone.now(),
                )
        return subscription

    @classmethod
    def get_quota_limit(cls, organization, metric: str) -> int:
        """Return the maximum permitted quantity for the specified metric.

        Returns -1 if the quota is unlimited (e.g. ENTERPRISE plan).
        """
        subscription = cls.get_or_create_subscription(organization)
        plan_quotas = PLAN_QUOTAS.get(subscription.plan, PLAN_QUOTAS[PlanChoices.FREE])
        return plan_quotas.get(metric, 0)

    @classmethod
    def get_current_usage(cls, organization, metric: str) -> int:
        """Get the current recorded quantity for a metric."""
        record = UsageRecord.objects.filter(organization=organization, metric=metric).first()
        return record.quantity if record else 0

    @classmethod
    def check_quota(cls, organization, metric: str, amount: int = 1) -> tuple[bool, int, int]:
        """Check whether the organization has remaining quota for the operation.

        Returns:
            (is_allowed, current_usage, quota_limit)
        """
        limit = cls.get_quota_limit(organization, metric)
        if limit == -1:
            # Unlimited
            current = cls.get_current_usage(organization, metric)
            return True, current, -1

        current = cls.get_current_usage(organization, metric)
        is_allowed = (current + amount) <= limit
        return is_allowed, current, limit

    @classmethod
    def increment_usage(cls, organization, metric: str, amount: int = 1) -> UsageRecord:
        """Atomically increment usage for a metric."""
        with transaction.atomic():
            record, created = UsageRecord.objects.select_for_update().get_or_create(
                organization=organization,
                metric=metric,
                defaults={"quantity": 0, "period_start": timezone.now()},
            )
            # Use F expression for atomic increment
            record.quantity = F("quantity") + amount
            record.updated_at = timezone.now()
            record.save(update_fields=["quantity", "updated_at"])
            record.refresh_from_db(fields=["quantity"])

        logger.info(
            f"Quota incremented: org={organization.id} metric={metric} "
            f"+{amount} -> total={record.quantity}"
        )
        return record

    @classmethod
    def check_and_increment(cls, organization, metric: str, amount: int = 1) -> UsageRecord:
        """Verify quota availability and increment atomically if within limits.

        Raises:
            QuotaExceededException: if the requested amount would exceed the plan threshold.
        """
        is_allowed, current, limit = cls.check_quota(organization, metric, amount)
        if not is_allowed:
            logger.warning(
                f"Quota exceeded: org={organization.id} metric={metric} "
                f"current={current} limit={limit} requested={amount}"
            )
            raise QuotaExceededException(
                metric=metric,
                current=current,
                limit=limit,
                requested=amount,
            )

        return cls.increment_usage(organization, metric, amount)

    @classmethod
    def get_usage_summary(cls, organization) -> dict[str, Any]:
        """Compile a full usage report across all tracked metrics."""
        subscription = cls.get_or_create_subscription(organization)
        plan_quotas = PLAN_QUOTAS.get(subscription.plan, PLAN_QUOTAS[PlanChoices.FREE])

        records_map = {
            r.metric: r.quantity for r in UsageRecord.objects.filter(organization=organization)
        }

        summary: dict[str, Any] = {}
        for metric_choice in UsageMetric.values:
            limit = plan_quotas.get(metric_choice, 0)
            current = records_map.get(metric_choice, 0)
            is_unlimited = limit == -1

            if is_unlimited:
                remaining = None
                percentage = 0.0
            else:
                remaining = max(0, limit - current)
                percentage = round((current / limit) * 100, 2) if limit > 0 else 100.0

            summary[metric_choice] = {
                "metric": metric_choice,
                "current": current,
                "limit": limit,
                "remaining": remaining,
                "percentage": percentage,
                "unlimited": is_unlimited,
            }

        return summary

    @classmethod
    def reset_usage(cls, organization, metric: str | None = None) -> None:
        """Reset usage metrics at billing cycle roll."""
        qs = UsageRecord.objects.filter(organization=organization)
        if metric:
            qs = qs.filter(metric=metric)
        qs.update(quantity=0, period_start=timezone.now(), updated_at=timezone.now())
        logger.info(f"Reset usage for org={organization.id} (metric={metric or 'all'})")
