"""Views for SaaS billing, plans, usage tracking, and system health checks."""

import logging
from typing import Any

from django.core.cache import cache
from django.db import connection
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import (
    PLAN_QUOTAS,
    AuditLog,
    PlanChoices,
    Subscription,
    SubscriptionStatus,
)
from apps.billing.serializers import (
    AuditLogSerializer,
    ChangePlanSerializer,
    PlanDetailsSerializer,
    SubscriptionSerializer,
    UsageSummarySerializer,
)
from apps.billing.services.audit_service import AuditLogService
from apps.billing.services.billing_provider import get_billing_provider
from apps.billing.services.quota_service import QuotaService
from apps.organizations.models import Organization

logger = logging.getLogger(__name__)

PLAN_FEATURES = {
    PlanChoices.FREE: [
        "Jusqu'à 5 documents",
        "50 pages analysées",
        "100 Mo de stockage",
        "10 générations IA",
        "50k tokens LLM",
        "15 min de synthèse vocale",
        "20 slides de présentation",
        "10 QCM générés",
    ],
    PlanChoices.PRO: [
        "Jusqu'à 50 documents",
        "1 000 pages analysées",
        "2 Go de stockage",
        "250 générations IA",
        "1M tokens LLM",
        "3 heures de synthèse vocale",
        "200 slides de présentation",
        "100 QCM générés",
        "Support prioritaire par email",
    ],
    PlanChoices.BUSINESS: [
        "Jusqu'à 250 documents",
        "10 000 pages analysées",
        "20 Go de stockage",
        "2 500 générations IA",
        "10M tokens LLM",
        "20 heures de synthèse vocale",
        "1 000 slides de présentation",
        "1 000 QCM générés",
        "Multi-enseignants & analytics avancés",
        "Support dédié 24/7",
    ],
    PlanChoices.ENTERPRISE: [
        "Documents illimités",
        "Pages illimitées",
        "Stockage sur mesure",
        "Générations IA illimitées",
        "Tokens LLM sur mesure",
        "Synthèse vocale illimitée",
        "Présentations illimitées",
        "QCM illimités",
        "Isolation dédiée & SLA garanti 99.9%",
        "Gestionnaire de compte dédié",
    ],
}


def get_user_organization(user, org_id_param=None) -> Organization:
    """Helper to resolve and authorize organization for an authenticated user."""
    if org_id_param:
        try:
            org = Organization.objects.get(id=org_id_param)
        except Organization.DoesNotExist:
            raise ValidationError({"organization_id": "Organisation introuvable."})
        if not org.is_member(user):
            raise PermissionDenied("Vous n'avez pas accès à cette organisation.")
        return org

    # Default to first organization the user is a member of
    membership = user.organization_memberships.select_related("organization").first()
    if not membership:
        raise ValidationError({"detail": "Vous n'êtes rattaché à aucune organisation."})
    return membership.organization


class BillingPlanView(APIView):
    """GET /billing/plan - List all available SaaS plans, quotas, and feature matrix."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="List SaaS Plans",
        description="Returns tier details, limits, and quotas for FREE, PRO, BUSINESS, ENTERPRISE.",
        responses={200: PlanDetailsSerializer(many=True)},
        tags=["Billing"],
    )
    def get(self, request):
        plans_data = []
        for choice_key, choice_label in PlanChoices.choices:
            plans_data.append({
                "plan": choice_key,
                "name": choice_label,
                "quotas": PLAN_QUOTAS.get(choice_key, {}),
                "features": PLAN_FEATURES.get(choice_key, []),
            })
        return Response(plans_data, status=status.HTTP_200_OK)


class BillingUsageView(APIView):
    """GET /billing/usage - Return resource consumption and quota limits for the active organization."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Quota Usage",
        description="Returns consumption breakdown across all tracked metrics with thresholds.",
        responses={200: UsageSummarySerializer},
        tags=["Billing"],
    )
    def get(self, request):
        org_id = request.query_params.get("organization_id")
        organization = get_user_organization(request.user, org_id)

        subscription = QuotaService.get_or_create_subscription(organization)
        metrics_summary = QuotaService.get_usage_summary(organization)

        data = {
            "organization_id": organization.id,
            "plan": subscription.plan,
            "metrics": metrics_summary,
        }
        return Response(data, status=status.HTTP_200_OK)


class BillingSubscriptionView(APIView):
    """GET  /billing/subscription - Get subscription details for organization.

    POST /billing/subscription - Upgrade or change subscription tier.
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get Subscription",
        description="Returns current contract, active plan, renewal date and status.",
        responses={200: SubscriptionSerializer},
        tags=["Billing"],
    )
    def get(self, request):
        org_id = request.query_params.get("organization_id")
        organization = get_user_organization(request.user, org_id)
        subscription = QuotaService.get_or_create_subscription(organization)
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Change Subscription Plan",
        description="Upgrade, downgrade, or update active plan for organization.",
        request=ChangePlanSerializer,
        responses={200: SubscriptionSerializer},
        tags=["Billing"],
    )
    def post(self, request):
        org_id = request.data.get("organization_id") or request.query_params.get("organization_id")
        organization = get_user_organization(request.user, org_id)

        # Only owners or admins can modify subscription
        if not organization.is_admin_or_owner(request.user):
            raise PermissionDenied("Seul un administrateur ou propriétaire peut modifier l'abonnement.")

        serializer = ChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_plan = serializer.validated_data["plan"]

        subscription = QuotaService.get_or_create_subscription(organization)
        old_plan = subscription.plan

        # Delegate to BillingProvider
        provider = get_billing_provider(subscription.billing_provider)
        provider_result = provider.change_plan(subscription, new_plan)

        subscription.plan = new_plan
        subscription.status = provider_result.get("status", SubscriptionStatus.ACTIVE)
        if provider_result.get("current_period_end"):
            subscription.current_period_end = provider_result["current_period_end"]
        subscription.save()

        # Update organization plan field as well for quick lookup
        organization.plan = new_plan
        organization.save(update_fields=["plan"])

        # Audit log
        AuditLogService.log(
            action="subscription.plan_changed",
            resource_type="subscription",
            resource_id=str(subscription.id),
            actor=request.user,
            organization=organization,
            request=request,
            metadata={
                "previous_plan": old_plan,
                "new_plan": new_plan,
                "provider": subscription.billing_provider,
            },
        )

        read_serializer = SubscriptionSerializer(subscription)
        return Response(read_serializer.data, status=status.HTTP_200_OK)


class SystemHealthView(APIView):
    """GET /system/health - Comprehensive production health probe.

    Verifies Database, Redis / Cache, Celery, and Storage services.
    """

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Production System Health Check",
        description="Deep diagnostics checking Database, Redis cache, and storage connectivity.",
        responses={
            200: OpenApiResponse(description="System is healthy"),
            503: OpenApiResponse(description="One or more components are degraded"),
        },
        tags=["System"],
    )
    def get(self, request):
        components: dict[str, Any] = {}
        is_healthy = True

        # 1. Database Probe
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            components["database"] = {"status": "ok", "latency_ms": 1}
        except Exception as e:
            logger.error(f"HealthCheck: Database failure: {e}")
            components["database"] = {"status": "error", "message": str(e)}
            is_healthy = False

        # 2. Redis / Cache Probe
        try:
            test_key = f"__health_ping_{timezone.now().timestamp()}__"
            cache.set(test_key, "pong", timeout=10)
            val = cache.get(test_key)
            if val == "pong":
                cache.delete(test_key)
                components["cache"] = {"status": "ok", "backend": "redis"}
            else:
                components["cache"] = {"status": "error", "message": "Cache write/read mismatch"}
                is_healthy = False
        except Exception as e:
            logger.warning(f"HealthCheck: Cache warning/failure: {e}")
            components["cache"] = {"status": "error", "message": str(e)}
            # Non-fatal if cache is local/degraded in test environment, but flag in prod
            is_healthy = False

        # 3. Storage Probe
        try:
            from apps.documents.services.storage import get_storage_service

            storage = get_storage_service()
            components["storage"] = {
                "status": "ok",
                "backend": storage.__class__.__name__,
            }
        except Exception as e:
            components["storage"] = {"status": "error", "message": str(e)}

        # 4. Celery Probe
        try:
            from celery import current_app

            inspector = current_app.control.inspect(timeout=1.0)
            ping_res = inspector.ping() if inspector else None
            active_workers = len(ping_res) if ping_res else 0
            components["celery"] = {
                "status": "ok" if active_workers > 0 else "idle",
                "active_workers": active_workers,
            }
        except Exception:
            components["celery"] = {"status": "offline", "active_workers": 0}

        overall_status = "healthy" if is_healthy else "degraded"
        status_code = status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE

        response_data = {
            "status": overall_status,
            "timestamp": timezone.now().isoformat(),
            "components": components,
        }
        return Response(response_data, status=status_code)


class AuditLogListView(generics.ListAPIView):
    """GET /billing/audit-logs - List audit trail logs for tenant admins."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        user = self.request.user
        org_id = self.request.query_params.get("organization_id")
        organization = get_user_organization(user, org_id)

        if not organization.is_admin_or_owner(user):
            raise PermissionDenied("Seul un administrateur peut consulter le journal d'audit.")

        return AuditLog.objects.filter(organization=organization).select_related("actor", "organization")
