"""Throttling classes for rate limiting AI generation and preventing resource abuse."""

import logging

from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger(__name__)


class AIGenerationRateThrottle(SimpleRateThrottle):
    """Throttles user AI generation requests to protect upstream LLM and GPU infrastructure.

    Returns HTTP 429 with standard Retry-After header upon exceeding rate.
    """

    scope = "ai_generation"
    rate = "30/minute"

    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            # Anonymous users throttled strictly by IP address
            ident = self.get_ident(request)
            return f"throttle_ai_anon_{ident}"

        # Authenticated users throttled by user ID
        return f"throttle_ai_user_{request.user.id}"


class AIBurstThrottle(SimpleRateThrottle):
    """Prevents sudden burst attacks and accidental double-click generations.

    Allows maximum 5 requests in a 10-second rolling window.
    """

    scope = "ai_burst"
    rate = "10/minute"

    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return f"throttle_burst_anon_{self.get_ident(request)}"
        return f"throttle_burst_user_{request.user.id}"
