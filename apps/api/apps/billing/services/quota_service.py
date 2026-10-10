"""Quota Management Service.

Enforces resource limits, atomic two-phase reservations, tracks usage records,
and prevents resource exhaustion across organizations and users according to
their active subscription plan.
"""

import logging
from typing import Any

from django.db import models, transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import APIException

from apps.billing.models import (
    PLAN_QUOTAS,
    USER_DAILY_LIMITS,
    PlanChoices,
    QuotaReservation,
    ReservationStatus,
    Subscription,
    SubscriptionStatus,
    UsageMetric,
    UsageRecord,
)

logger = logging.getLogger(__name__)


class QuotaExceededException(APIException):
    """Raised when an organization or user attempts to exceed its plan quota limits.

    Maps to HTTP 429 Too Many Requests per SaaS API specifications.
    """

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_code = "quota_exceeded"

    def __init__(
        self,
        metric: str,
        current: int,
        limit: int,
        requested: int = 1,
        detail: str | None = None,
        is_user_limit: bool = False,
    ):
        self.metric = metric
        self.current = current
        self.limit = limit
        self.requested = requested
        self.is_user_limit = is_user_limit

        scope = "Utilisateur" if is_user_limit else "Organisation"
        if detail is None:
            detail = (
                f"Quota dépassé pour '{metric}' ({scope}). Limite du plan : {limit}, "
                f"consommation actuelle : {current}, demandé : {requested}. "
                f"Veuillez mettre à niveau votre abonnement ou patienter."
            )
        super().__init__(detail=detail, code="quota_exceeded")


class QuotaService:
    """Service to inspect, reserve, commit, release, and summarize quota consumption per organization."""

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
        """Get the current recorded quantity for a metric (committed consumption)."""
        record = UsageRecord.objects.filter(organization=organization, metric=metric).first()
        return record.quantity if record else 0

    @classmethod
    def check_quota(
        cls,
        organization,
        metric: str,
        amount: int = 1,
        user: Any = None,
    ) -> tuple[bool, int, int]:
        """Check whether the organization has remaining quota for the operation.

        Takes into account both confirmed consumption and active pending reservations.

        Returns:
            (is_allowed, effective_usage, quota_limit)
        """
        limit = cls.get_quota_limit(organization, metric)
        current = cls.get_current_usage(organization, metric)

        # Sum active pending reservations
        pending_reserved = (
            QuotaReservation.objects.filter(
                organization=organization,
                metric=metric,
                status=ReservationStatus.PENDING,
            ).aggregate(total=models.Sum("reserved_amount"))["total"]
            or 0
        )
        effective = current + pending_reserved

        if limit == -1:
            return True, effective, -1

        is_allowed = (effective + amount) <= limit

        # Also check user daily quota if user given
        if is_allowed and user and getattr(user, "is_authenticated", False):
            subscription = cls.get_or_create_subscription(organization)
            user_limits = USER_DAILY_LIMITS.get(subscription.plan, USER_DAILY_LIMITS[PlanChoices.FREE])
            user_limit = user_limits.get(metric, -1)
            if user_limit != -1:
                today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
                daily_used = (
                    QuotaReservation.objects.filter(
                        organization=organization,
                        user=user,
                        metric=metric,
                        created_at__gte=today_start,
                        status__in=[
                            ReservationStatus.PENDING,
                            ReservationStatus.COMMITTED,
                            ReservationStatus.TIMEOUT_UNCERTAIN,
                        ],
                    ).aggregate(total=models.Sum("reserved_amount"))["total"]
                    or 0
                )
                if (daily_used + amount) > user_limit:
                    return False, daily_used, user_limit

        return is_allowed, effective, limit

    @classmethod
    def _check_user_daily_limit(cls, organization, user, metric: str, amount: int = 1) -> None:
        """Enforces per-user daily limits within the organization."""
        if not user or not getattr(user, "is_authenticated", False):
            return
        subscription = cls.get_or_create_subscription(organization)
        user_limits = USER_DAILY_LIMITS.get(subscription.plan, USER_DAILY_LIMITS[PlanChoices.FREE])
        user_limit = user_limits.get(metric, -1)

        if user_limit == -1:
            return

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_used = (
            QuotaReservation.objects.filter(
                organization=organization,
                user=user,
                metric=metric,
                created_at__gte=today_start,
                status__in=[
                    ReservationStatus.PENDING,
                    ReservationStatus.COMMITTED,
                    ReservationStatus.TIMEOUT_UNCERTAIN,
                ],
            ).aggregate(total=models.Sum("reserved_amount"))["total"]
            or 0
        )

        if (daily_used + amount) > user_limit:
            raise QuotaExceededException(
                metric=metric,
                current=daily_used,
                limit=user_limit,
                requested=amount,
                is_user_limit=True,
            )

    @classmethod
    def reserve_quota(
        cls,
        organization,
        metric: str,
        amount: int = 1,
        user: Any = None,
        idempotency_key: str | None = None,
        task_id: str | None = None,
        estimated_cost_usd: float = 0.0,
    ) -> QuotaReservation:
        """Atomically reserve quota before triggering AI generation.

        Guarantees:
        - Atomic concurrency locking via select_for_update() on UsageRecord
        - Idempotency replay (returns existing reservation without double deducting)
        - Prevents multiple requests from exceeding the last available quota slot
        - Enforces user-level daily quotas when applicable
        """
        import uuid as _uuid

        safe_key = idempotency_key or f"res_{_uuid.uuid4().hex}"

        with transaction.atomic():
            # 1. Idempotency replay check
            existing = QuotaReservation.objects.filter(idempotency_key=safe_key).first()
            if existing:
                if existing.status in (ReservationStatus.COMMITTED, ReservationStatus.PENDING):
                    logger.info(
                        f"Reusing existing reservation {existing.id} (key={safe_key}, status={existing.status})"
                    )
                    return existing

            limit = cls.get_quota_limit(organization, metric)
            record, _ = UsageRecord.objects.select_for_update().get_or_create(
                organization=organization,
                metric=metric,
                defaults={"quantity": 0, "period_start": timezone.now()},
            )

            # Sum pending reservations currently active
            pending_reserved = (
                QuotaReservation.objects.filter(
                    organization=organization,
                    metric=metric,
                    status=ReservationStatus.PENDING,
                ).aggregate(total=models.Sum("reserved_amount"))["total"]
                or 0
            )

            effective = record.quantity + pending_reserved
            if limit != -1 and (effective + amount) > limit:
                logger.warning(
                    f"Quota reservation rejected: org={organization.id} metric={metric} "
                    f"effective={effective} limit={limit} requested={amount}"
                )
                raise QuotaExceededException(
                    metric=metric,
                    current=effective,
                    limit=limit,
                    requested=amount,
                )

            # Check user daily limit
            if user:
                cls._check_user_daily_limit(organization, user, metric, amount)

            reservation = QuotaReservation.objects.create(
                organization=organization,
                user=user if getattr(user, "is_authenticated", False) else None,
                metric=metric,
                reserved_amount=amount,
                idempotency_key=safe_key,
                task_id=str(task_id or ""),
                status=ReservationStatus.PENDING,
                estimated_cost_usd=estimated_cost_usd,
                is_cost_estimated=True,
            )
            logger.info(
                f"Quota reserved: id={reservation.id} org={organization.id} "
                f"metric={metric} amount={amount} key={safe_key}"
            )
            return reservation

    @classmethod
    def commit_quota(
        cls,
        reservation: QuotaReservation | str,
        actual_amount: int | None = None,
        actual_cost_usd: float | None = None,
        is_confirmed_by_provider: bool = False,
    ) -> QuotaReservation:
        """Confirm successful generation consumption and persist to official UsageRecord.

        Idempotent: committing an already committed reservation returns without double counting.
        """
        with transaction.atomic():
            res_id = reservation.id if hasattr(reservation, "id") else reservation
            res = QuotaReservation.objects.select_for_update().get(id=res_id)

            if res.status == ReservationStatus.COMMITTED:
                logger.info(f"Reservation {res.id} already committed. Idempotent no-op.")
                return res

            final_amount = actual_amount if actual_amount is not None else res.reserved_amount

            record, _ = UsageRecord.objects.select_for_update().get_or_create(
                organization=res.organization,
                metric=res.metric,
                defaults={"quantity": 0, "period_start": timezone.now()},
            )
            record.quantity = F("quantity") + final_amount
            record.updated_at = timezone.now()
            record.save(update_fields=["quantity", "updated_at"])

            res.status = ReservationStatus.COMMITTED
            res.actual_amount = final_amount
            if actual_cost_usd is not None:
                res.actual_cost_usd = actual_cost_usd
                res.is_cost_estimated = not is_confirmed_by_provider
            res.updated_at = timezone.now()
            res.save(
                update_fields=[
                    "status",
                    "actual_amount",
                    "actual_cost_usd",
                    "is_cost_estimated",
                    "updated_at",
                ]
            )

            logger.info(
                f"Quota committed: id={res.id} org={res.organization_id} amount={final_amount}"
            )
            return res

    @classmethod
    def release_quota(
        cls,
        reservation: QuotaReservation | str,
        reason: str = "failed",
    ) -> QuotaReservation:
        """Release or refund quota when generation fails or is cancelled."""
        with transaction.atomic():
            res_id = reservation.id if hasattr(reservation, "id") else reservation
            res = QuotaReservation.objects.select_for_update().get(id=res_id)

            if res.status == ReservationStatus.RELEASED:
                return res

            if res.status == ReservationStatus.COMMITTED:
                # Refund from UsageRecord
                amount_to_refund = res.actual_amount or res.reserved_amount
                record = (
                    UsageRecord.objects.select_for_update()
                    .filter(
                        organization=res.organization,
                        metric=res.metric,
                    )
                    .first()
                )
                if record:
                    record.quantity = models.Case(
                        models.When(
                            quantity__gte=amount_to_refund,
                            then=F("quantity") - amount_to_refund,
                        ),
                        default=0,
                        output_field=models.BigIntegerField(),
                    )
                    record.updated_at = timezone.now()
                    record.save(update_fields=["quantity", "updated_at"])

            res.status = ReservationStatus.RELEASED
            res.error_detail = str(reason)
            res.updated_at = timezone.now()
            res.save(update_fields=["status", "error_detail", "updated_at"])
            logger.info(f"Quota released: id={res.id} reason={reason}")
            return res

    @classmethod
    def mark_timeout_uncertain(
        cls,
        reservation: QuotaReservation | str,
        error_detail: str = "Provider timeout without acknowledgement",
    ) -> QuotaReservation:
        """Quarantine reservation when provider call timed out without certainty.

        Preserves cost estimation and flags status=TIMEOUT_UNCERTAIN without double counting.
        """
        with transaction.atomic():
            res_id = reservation.id if hasattr(reservation, "id") else reservation
            res = QuotaReservation.objects.select_for_update().get(id=res_id)

            res.status = ReservationStatus.TIMEOUT_UNCERTAIN
            res.is_cost_estimated = True
            res.error_detail = str(error_detail)
            res.updated_at = timezone.now()
            res.save(
                update_fields=["status", "is_cost_estimated", "error_detail", "updated_at"]
            )
            logger.warning(
                f"Reservation marked TIMEOUT_UNCERTAIN: id={res.id} reason={error_detail}"
            )
            return res

    @classmethod
    def increment_usage(cls, organization, metric: str, amount: int = 1) -> UsageRecord:
        """Atomically increment usage for a metric directly."""
        with transaction.atomic():
            record, _ = UsageRecord.objects.select_for_update().get_or_create(
                organization=organization,
                metric=metric,
                defaults={"quantity": 0, "period_start": timezone.now()},
            )
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
    def check_and_increment(
        cls,
        organization,
        metric: str,
        amount: int = 1,
        user: Any = None,
        idempotency_key: str | None = None,
    ) -> UsageRecord:
        """Verify quota availability and increment atomically if within limits.

        Fully atomic inside transaction.atomic() to prevent race conditions.
        """
        with transaction.atomic():
            limit = cls.get_quota_limit(organization, metric)
            record, _ = UsageRecord.objects.select_for_update().get_or_create(
                organization=organization,
                metric=metric,
                defaults={"quantity": 0, "period_start": timezone.now()},
            )

            pending_reserved = (
                QuotaReservation.objects.filter(
                    organization=organization,
                    metric=metric,
                    status=ReservationStatus.PENDING,
                ).aggregate(total=models.Sum("reserved_amount"))["total"]
                or 0
            )

            effective = record.quantity + pending_reserved
            if limit != -1 and (effective + amount) > limit:
                logger.warning(
                    f"Quota exceeded: org={organization.id} metric={metric} "
                    f"current={effective} limit={limit} requested={amount}"
                )
                raise QuotaExceededException(
                    metric=metric,
                    current=effective,
                    limit=limit,
                    requested=amount,
                )

            if user:
                cls._check_user_daily_limit(organization, user, metric, amount)

            record.quantity = F("quantity") + amount
            record.updated_at = timezone.now()
            record.save(update_fields=["quantity", "updated_at"])
            record.refresh_from_db(fields=["quantity"])
            return record

    @classmethod
    def get_usage_summary(cls, organization) -> dict[str, Any]:
        """Compile a full usage report across all tracked metrics, reservations, and costs."""
        subscription = cls.get_or_create_subscription(organization)
        plan_quotas = PLAN_QUOTAS.get(subscription.plan, PLAN_QUOTAS[PlanChoices.FREE])

        records_map = {
            r.metric: r.quantity for r in UsageRecord.objects.filter(organization=organization)
        }

        # Pending reservations per metric
        pending_map = {
            row["metric"]: row["total"]
            for row in QuotaReservation.objects.filter(
                organization=organization,
                status=ReservationStatus.PENDING,
            )
            .values("metric")
            .annotate(total=models.Sum("reserved_amount"))
        }

        summary: dict[str, Any] = {}
        for metric_choice in UsageMetric.values:
            limit = plan_quotas.get(metric_choice, 0)
            current = records_map.get(metric_choice, 0)
            pending = pending_map.get(metric_choice, 0)
            effective = current + pending
            is_unlimited = limit == -1

            if is_unlimited:
                remaining = None
                percentage = 0.0
            else:
                remaining = max(0, limit - effective)
                percentage = round((effective / limit) * 100, 2) if limit > 0 else 100.0

            summary[metric_choice] = {
                "metric": metric_choice,
                "current": current,
                "pending_reserved": pending,
                "effective_usage": effective,
                "limit": limit,
                "remaining": remaining,
                "percentage": percentage,
                "unlimited": is_unlimited,
            }

        # Financial audit metrics
        reservations_qs = QuotaReservation.objects.filter(organization=organization)
        total_estimated_usd = (
            reservations_qs.filter(is_cost_estimated=True).aggregate(
                total=models.Sum("estimated_cost_usd")
            )["total"]
            or 0.0
        )
        total_confirmed_usd = (
            reservations_qs.filter(is_cost_estimated=False).aggregate(
                total=models.Sum("actual_cost_usd")
            )["total"]
            or 0.0
        )
        timeouts_count = reservations_qs.filter(
            status=ReservationStatus.TIMEOUT_UNCERTAIN
        ).count()

        summary["cost_audit"] = {
            "estimated_cost_usd": float(round(total_estimated_usd, 4)),
            "confirmed_cost_usd": float(round(total_confirmed_usd, 4)),
            "timeout_uncertain_count": timeouts_count,
        }
        return summary

    @classmethod
    def reset_usage(cls, organization, metric: str | None = None) -> None:
        """Reset usage metrics at billing cycle roll."""
        qs = UsageRecord.objects.filter(organization=organization)
        if metric:
            qs = qs.filter(metric=metric)
        qs.update(quantity=0, period_start=timezone.now(), updated_at=timezone.now())

        # Also release any lingering pending reservations for clean slate
        res_qs = QuotaReservation.objects.filter(organization=organization)
        if metric:
            res_qs = res_qs.filter(metric=metric)
        res_qs.filter(status=ReservationStatus.PENDING).update(
            status=ReservationStatus.RELEASED,
            error_detail="Cycle reset",
            updated_at=timezone.now(),
        )
        logger.info(f"Reset usage for org={organization.id} (metric={metric or 'all'})")
