import hashlib
import logging

from django.conf import settings
from django.core.cache import cache

from .base import EmbeddingProvider

logger = logging.getLogger(__name__)

CACHE_PREFIX = "emb"
DEFAULT_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days


class CachedEmbeddingProvider(EmbeddingProvider):
    """Read-through cache (Django cache / Redis in production) around an EmbeddingProvider.

    Embeddings are deterministic for a given (model, dimensions, text) triple, so
    repeated inputs safely reuse the cached vector instead of paying the provider
    round-trip. The cache is strictly best-effort: any failure logs a warning and
    falls through to the wrapped provider, never blocking embedding generation.
    """

    def __init__(self, inner: EmbeddingProvider):
        self._inner = inner
        self.dimensions = inner.dimensions
        self.model_name = inner.model_name

    @property
    def _ttl(self) -> int:
        return int(getattr(settings, "EMBEDDING_CACHE_TTL", DEFAULT_TTL_SECONDS))

    def _cache_key(self, text: str) -> str:
        fingerprint = hashlib.sha256(
            f"{type(self._inner).__name__}:{self.model_name}:{self.dimensions}:{text}".encode(
                "utf-8"
            )
        ).hexdigest()
        return f"{CACHE_PREFIX}:{fingerprint}"

    def _get_cached(self, key: str) -> list[float] | None:
        try:
            value = cache.get(key)
        except Exception as e:
            logger.warning(f"[CachedEmbeddingProvider] cache get failed ({e}); bypassing cache.")
            return None
        if isinstance(value, list):
            return value
        return None

    def _set_cached(self, key: str, vector: list[float]) -> None:
        try:
            cache.set(key, vector, self._ttl)
        except Exception as e:
            logger.warning(f"[CachedEmbeddingProvider] cache set failed ({e}); bypassing cache.")

    def embed_text(self, text: str) -> list[float]:
        key = self._cache_key(text)
        cached = self._get_cached(key)
        if cached is not None:
            return cached
        vector = self._inner.embed_text(text)
        if vector:
            self._set_cached(key, vector)
        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float] | None] = [None] * len(texts)
        missing_indices: list[int] = []

        for index, text in enumerate(texts):
            cached = self._get_cached(self._cache_key(text))
            if cached is not None:
                results[index] = cached
            else:
                missing_indices.append(index)

        if missing_indices:
            missing_texts = [texts[i] for i in missing_indices]
            computed = self._inner.embed_batch(missing_texts)
            for position, index in enumerate(missing_indices):
                if position >= len(computed):
                    continue
                vector = computed[position]
                results[index] = vector
                if vector:
                    self._set_cached(self._cache_key(texts[index]), vector)

        # Any entry the inner provider failed to return falls back to zeros.
        return [vector if vector is not None else [0.0] * self.dimensions for vector in results]
