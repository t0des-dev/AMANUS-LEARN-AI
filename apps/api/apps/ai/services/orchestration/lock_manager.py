import contextlib
import logging
import time
from typing import Any

from django.core.cache import cache

logger = logging.getLogger(__name__)


class ConcurrentGenerationConflictError(Exception):
    """Raised when an operation is requested while a generation task is already active."""

    def __init__(
        self, resource_type: str, resource_id: str, lock_info: dict[str, Any] | None = None
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.lock_info = lock_info or {}
        message = f"Une génération est déjà en cours d'exécution pour la ressource {resource_type}:{resource_id}."
        super().__init__(message)


class GenerationLock:
    """Distributed lock manager preventing concurrent duplicate AI executions on the same resource.

    Uses Django's cache layer (Redis or cache backend) with atomic `cache.add`.
    """

    DEFAULT_TIMEOUT_SECONDS = 300  # 5 minutes safety release

    @classmethod
    def _make_key(cls, resource_type: str, resource_id: str) -> str:
        return f"gen_lock:{str(resource_type).lower()}:{str(resource_id)}"

    @classmethod
    def acquire(
        cls,
        resource_type: str,
        resource_id: str,
        owner_id: str | None = None,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> bool:
        """Attempts to acquire lock atomically.

        Returns True if acquired.
        Raises ConcurrentGenerationConflictError if already locked.
        """
        key = cls._make_key(resource_type, resource_id)
        lock_payload = {
            "resource_type": str(resource_type),
            "resource_id": str(resource_id),
            "owner_id": str(owner_id or "anonymous"),
            "acquired_at": time.time(),
        }

        # cache.add is atomic: returns True only if key did not previously exist
        acquired = cache.add(key, lock_payload, timeout=timeout)
        if not acquired:
            existing = cache.get(key)
            logger.warning(
                "Lock collision on %s:%s (current lock: %s)",
                resource_type,
                resource_id,
                existing,
            )
            raise ConcurrentGenerationConflictError(resource_type, resource_id, existing)

        logger.info(
            "Acquired generation lock for %s:%s (TTL: %ss)", resource_type, resource_id, timeout
        )
        return True

    @classmethod
    def release(cls, resource_type: str, resource_id: str) -> None:
        """Releases the lock."""
        key = cls._make_key(resource_type, resource_id)
        cache.delete(key)
        logger.info("Released generation lock for %s:%s", resource_type, resource_id)

    @classmethod
    def is_locked(cls, resource_type: str, resource_id: str) -> bool:
        """Checks if a lock is currently active."""
        key = cls._make_key(resource_type, resource_id)
        return cache.get(key) is not None


@contextlib.contextmanager
def generation_lock(
    resource_type: str, resource_id: str, owner_id: str | None = None, timeout: int = 300
):
    """Context manager for acquiring and releasing generation lock safely."""
    GenerationLock.acquire(resource_type, resource_id, owner_id=owner_id, timeout=timeout)
    try:
        yield
    finally:
        GenerationLock.release(resource_type, resource_id)


class IdempotencyManager:
    """Stores and checks idempotency keys to prevent duplicate execution upon network retries."""

    DEFAULT_TTL_SECONDS = 86400  # 24 hours

    @classmethod
    def _make_key(cls, idempotency_key: str) -> str:
        return f"idempotency:{str(idempotency_key).strip()}"

    @classmethod
    def get_existing_result(cls, idempotency_key: str) -> dict[str, Any] | None:
        """Retrieves previously cached execution result for this idempotency key."""
        if not idempotency_key or not str(idempotency_key).strip():
            return None
        return cache.get(cls._make_key(idempotency_key))

    @classmethod
    def record_result(
        cls, idempotency_key: str, result_data: dict[str, Any], ttl: int = DEFAULT_TTL_SECONDS
    ) -> None:
        """Caches result payload for idempotency key."""
        if not idempotency_key or not str(idempotency_key).strip():
            return
        cache.set(cls._make_key(idempotency_key), result_data, timeout=ttl)
