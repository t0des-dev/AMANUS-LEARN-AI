"""Serializers for SaaS billing, plans, usage, and subscriptions."""

from rest_framework import serializers

from apps.billing.models import (
    PLAN_QUOTAS,
    AuditLog,
    PlanChoices,
    Subscription,
    SubscriptionStatus,
    UsageRecord,
)


class PlanDetailsSerializer(serializers.Serializer):
    """Details and quotas for a specific subscription plan tier."""

    plan = serializers.CharField()
    name = serializers.CharField()
    quotas = serializers.DictField()
    features = serializers.ListField(child=serializers.CharField())


class SubscriptionSerializer(serializers.ModelSerializer):
    """Full subscription contract representation."""

    organization_id = serializers.UUIDField(source="organization.id", read_only=True)
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    plan_display = serializers.CharField(source="get_plan_display", read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "organization_id",
            "organization_name",
            "plan",
            "plan_display",
            "status",
            "is_active",
            "started_at",
            "current_period_end",
            "canceled_at",
            "billing_provider",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ChangePlanSerializer(serializers.Serializer):
    """Input payload to upgrade or change subscription plan."""

    plan = serializers.ChoiceField(choices=PlanChoices.choices)


class UsageMetricSerializer(serializers.Serializer):
    """Metric quota breakdown."""

    metric = serializers.CharField()
    current = serializers.IntegerField()
    limit = serializers.IntegerField()
    remaining = serializers.IntegerField(allow_null=True)
    percentage = serializers.FloatField()
    unlimited = serializers.BooleanField()


class UsageSummarySerializer(serializers.Serializer):
    """Aggregated usage overview for an organization."""

    organization_id = serializers.UUIDField()
    plan = serializers.CharField()
    metrics = serializers.DictField(child=UsageMetricSerializer())


class UsageRecordSerializer(serializers.ModelSerializer):
    """Individual metric usage record."""

    class Meta:
        model = UsageRecord
        fields = (
            "id",
            "metric",
            "quantity",
            "period_start",
            "period_end",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class AuditLogSerializer(serializers.ModelSerializer):
    """Immutable audit trail log entry."""

    actor_email = serializers.CharField(source="actor.email", default=None, read_only=True)
    actor_name = serializers.CharField(source="actor.get_full_name", default=None, read_only=True)

    class Meta:
        model = AuditLog
        fields = (
            "id",
            "organization",
            "actor",
            "actor_email",
            "actor_name",
            "action",
            "resource_type",
            "resource_id",
            "ip_address",
            "user_agent",
            "metadata",
            "created_at",
        )
        read_only_fields = fields
