import hashlib
import json
import logging
from typing import Any

from django.core.cache import cache

logger = logging.getLogger(__name__)


class GenerationCacheService:
    """Safe, tenant-isolated result cache for deterministic AI generation outputs.

    STRICT GUARANTEES:
    1. Organization ID is strictly embedded into every cache key, preventing cross-tenant leakage.
    2. Cache is fingerprinted against content hash, prompt version, model, and parameters.
    3. Content changes immediately invalidate the fingerprint.
    """

    DEFAULT_CACHE_TTL_SECONDS = 86400 * 7  # 7 days

    @classmethod
    def compute_fingerprint(
        cls,
        organization_id: str,
        resource_type: str,
        content: str,
        prompt_version: str,
        model: str,
        language: str = "fr",
        extra_params: dict[str, Any] | None = None,
    ) -> str:
        """Computes deterministic SHA-256 fingerprint for a generation configuration."""
        clean_org = str(organization_id).strip()
        clean_type = str(resource_type).strip().lower()
        clean_content = str(content or "").strip()
        clean_prompt = str(prompt_version or "").strip()
        clean_model = str(model or "").strip().lower()
        clean_lang = str(language or "fr").strip().lower()

        # Sort extra params for deterministic serialization
        serialized_extras = ""
        if extra_params:
            try:
                serialized_extras = json.dumps(extra_params, sort_keys=True)
            except Exception:
                serialized_extras = str(extra_params)

        hasher = hashlib.sha256()
        hasher.update(clean_org.encode("utf-8"))
        hasher.update(b"|")
        hasher.update(clean_type.encode("utf-8"))
        hasher.update(b"|")
        hasher.update(clean_content.encode("utf-8"))
        hasher.update(b"|")
        hasher.update(clean_prompt.encode("utf-8"))
        hasher.update(b"|")
        hasher.update(clean_model.encode("utf-8"))
        hasher.update(b"|")
        hasher.update(clean_lang.encode("utf-8"))
        hasher.update(b"|")
        hasher.update(serialized_extras.encode("utf-8"))

        return hasher.hexdigest()

    @classmethod
    def _make_key(cls, organization_id: str, fingerprint: str) -> str:
        return f"ai_gen_cache:{str(organization_id)}:{str(fingerprint)}"

    @classmethod
    def get_cached(cls, organization_id: str, fingerprint: str) -> dict[str, Any] | None:
        """Retrieves cached result if present and belonging strictly to this organization."""
        key = cls._make_key(organization_id, fingerprint)
        cached_entry = cache.get(key)
        if cached_entry:
            logger.info(
                "Generation cache HIT for org %s (fingerprint: %s...)",
                organization_id,
                fingerprint[:8],
            )
            return cached_entry
        return None

    @classmethod
    def set_cached(
        cls,
        organization_id: str,
        fingerprint: str,
        result_data: dict[str, Any],
        ttl: int = DEFAULT_CACHE_TTL_SECONDS,
    ) -> None:
        """Stores validated generation result under tenant-scoped cache key."""
        key = cls._make_key(organization_id, fingerprint)
        cache.set(key, result_data, timeout=ttl)
        logger.info("Generation cache STORED for org %s (TTL: %ss)", organization_id, ttl)

    @classmethod
    def invalidate(cls, organization_id: str, fingerprint: str) -> None:
        """Invalidates a specific cached generation."""
        key = cls._make_key(organization_id, fingerprint)
        cache.delete(key)
        logger.info("Generation cache INVALIDATED for org %s", organization_id)
