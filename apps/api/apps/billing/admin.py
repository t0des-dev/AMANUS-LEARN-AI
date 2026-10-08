from django.contrib import admin

from .models import AuditLog, Subscription, UsageRecord


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("organization", "plan", "status", "started_at", "current_period_end", "billing_provider")
    list_filter = ("plan", "status", "billing_provider")
    search_fields = ("organization__name", "provider_customer_id")


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ("organization", "metric", "quantity", "updated_at")
    list_filter = ("metric", "updated_at")
    search_fields = ("organization__name",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "organization", "actor", "action", "resource_type", "ip_address")
    list_filter = ("action", "resource_type", "created_at")
    search_fields = ("actor__email", "organization__name", "resource_id", "action")
    readonly_fields = ("id", "organization", "actor", "action", "resource_type", "resource_id", "ip_address", "user_agent", "metadata", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
