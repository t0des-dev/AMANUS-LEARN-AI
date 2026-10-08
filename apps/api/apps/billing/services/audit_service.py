"""Audit Logging Service.

Provides centralized recording of administrative and business-critical operations
for traceability, security reviews, and compliance auditing.
"""

import logging
from typing import Any

from django.http import HttpRequest

from apps.billing.models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogService:
    """Service to create and query immutable audit log entries."""

    @staticmethod
    def get_client_ip(request: HttpRequest | None) -> str | None:
        """Extract remote client IP address from request headers or socket info."""
        if not request:
            return None
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            # First IP in chain is the real client IP
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    @staticmethod
    def get_user_agent(request: HttpRequest | None) -> str:
        """Extract client User-Agent string safely."""
        if not request:
            return ""
        return request.META.get("HTTP_USER_AGENT", "")[:500]

    @classmethod
    def log(
        cls,
        action: str,
        resource_type: str,
        resource_id: str = "",
        actor=None,
        organization=None,
        request: HttpRequest | None = None,
        ip_address: str | None = None,
        user_agent: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> AuditLog:
        """Record an audit trail event.

        If `request` is provided, `actor`, `ip_address`, and `user_agent` are inferred automatically
        unless explicitly passed.
        """
        if request is not None:
            if actor is None and hasattr(request, "user") and request.user.is_authenticated:
                actor = request.user
            if ip_address is None:
                ip_address = cls.get_client_ip(request)
            if not user_agent:
                user_agent = cls.get_user_agent(request)
            if organization is None and hasattr(request, "organization"):
                organization = getattr(request, "organization", None)

        entry = AuditLog.objects.create(
            organization=organization,
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )

        logger.info(
            f"AUDIT: [{action}] resource={resource_type}:{resource_id} "
            f"actor={getattr(actor, 'email', 'System')} org={getattr(organization, 'id', None)}"
        )
        return entry
