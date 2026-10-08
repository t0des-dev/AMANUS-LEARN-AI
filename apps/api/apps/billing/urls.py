"""URL configuration for Billing, Quotas, and System Health."""

from django.urls import path

from apps.billing.views import (
    AuditLogListView,
    BillingPlanView,
    BillingSubscriptionView,
    BillingUsageView,
    SystemHealthView,
)

urlpatterns = [
    # Billing & Plans
    path("plan", BillingPlanView.as_view(), name="billing-plan"),
    path("plan/", BillingPlanView.as_view(), name="billing-plan-slash"),
    path("plans", BillingPlanView.as_view(), name="billing-plans"),
    path("plans/", BillingPlanView.as_view(), name="billing-plans-slash"),
    # Usage & Quotas
    path("usage", BillingUsageView.as_view(), name="billing-usage"),
    path("usage/", BillingUsageView.as_view(), name="billing-usage-slash"),
    # Subscription
    path("subscription", BillingSubscriptionView.as_view(), name="billing-subscription"),
    path("subscription/", BillingSubscriptionView.as_view(), name="billing-subscription-slash"),
    # Audit Logs
    path("audit-logs", AuditLogListView.as_view(), name="billing-audit-logs"),
    path("audit-logs/", AuditLogListView.as_view(), name="billing-audit-logs-slash"),
    # Health probe
    path("system/health", SystemHealthView.as_view(), name="system-health"),
    path("system/health/", SystemHealthView.as_view(), name="system-health-slash"),
]
