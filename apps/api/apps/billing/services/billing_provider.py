"""Billing Provider Abstraction Layer.

Defines the contract for SaaS billing integrations (Stripe, LemonSqueezy, Paddle, Mock)
without coupling the platform to any single payment processor.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any
import uuid

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class BaseBillingProvider(ABC):
    """Abstract interface defining required SaaS billing actions."""

    @abstractmethod
    def create_customer(self, organization) -> str:
        """Create a billing customer for the organization.

        Returns customer identifier (e.g. cus_xxx).
        """
        pass

    @abstractmethod
    def create_subscription(self, organization, plan: str) -> dict[str, Any]:
        """Create or initialize a subscription for an organization and plan.

        Returns a dictionary containing subscription details (id, status, current_period_end).
        """
        pass

    @abstractmethod
    def cancel_subscription(self, subscription) -> bool:
        """Cancel an existing active subscription."""
        pass

    @abstractmethod
    def change_plan(self, subscription, new_plan: str) -> dict[str, Any]:
        """Upgrade or downgrade an organization's subscription plan."""
        pass

    @abstractmethod
    def get_subscription_status(self, subscription) -> dict[str, Any]:
        """Fetch remote subscription status, renewal date, and invoices."""
        pass

    @abstractmethod
    def handle_webhook(self, payload: dict[str, Any], signature: str = "") -> dict[str, Any]:
        """Validate and parse incoming webhook events from the payment gateway."""
        pass


class MockBillingProvider(BaseBillingProvider):
    """In-memory mock billing provider for tests and local development."""

    def create_customer(self, organization) -> str:
        customer_id = f"mock_cus_{organization.id.hex[:12]}"
        logger.info(f"MockBillingProvider: Created customer {customer_id} for org {organization.name}")
        return customer_id

    def create_subscription(self, organization, plan: str) -> dict[str, Any]:
        sub_id = f"mock_sub_{uuid.uuid4().hex[:12]}"
        period_end = timezone.now() + timezone.timedelta(days=30)
        logger.info(f"MockBillingProvider: Created subscription {sub_id} for org {organization.name} on plan {plan}")
        return {
            "provider_subscription_id": sub_id,
            "status": "ACTIVE",
            "current_period_end": period_end,
            "plan": plan,
        }

    def cancel_subscription(self, subscription) -> bool:
        logger.info(f"MockBillingProvider: Canceled subscription {subscription.id}")
        return True

    def change_plan(self, subscription, new_plan: str) -> dict[str, Any]:
        logger.info(f"MockBillingProvider: Changed subscription {subscription.id} plan to {new_plan}")
        return {
            "provider_subscription_id": subscription.provider_subscription_id,
            "status": "ACTIVE",
            "plan": new_plan,
            "current_period_end": subscription.current_period_end,
        }

    def get_subscription_status(self, subscription) -> dict[str, Any]:
        return {
            "provider_subscription_id": subscription.provider_subscription_id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
            "plan": subscription.plan,
            "is_valid": True,
        }

    def handle_webhook(self, payload: dict[str, Any], signature: str = "") -> dict[str, Any]:
        event_type = payload.get("type", "ping")
        logger.info(f"MockBillingProvider: Handled webhook event {event_type}")
        return {
            "event": event_type,
            "handled": True,
            "data": payload.get("data", {}),
        }


def get_billing_provider(provider_name: str | None = None) -> BaseBillingProvider:
    """Factory returning the active billing provider instance."""
    name = (provider_name or getattr(settings, "BILLING_PROVIDER", "mock")).lower()
    if name == "mock":
        return MockBillingProvider()
    # Placeholder for future providers (e.g., stripe, lemonsqueezy)
    logger.warning(f"Billing provider '{name}' not found, falling back to MockBillingProvider.")
    return MockBillingProvider()
