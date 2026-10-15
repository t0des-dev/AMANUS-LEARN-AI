import os

from django.conf import settings

from .base import EmbeddingProvider
from .cache_provider import CachedEmbeddingProvider
from .mock_provider import DeterministicEmbeddingProvider
from .openai_provider import OpenAIEmbeddingProvider

_CACHED_PROVIDER: EmbeddingProvider | None = None


def get_embedding_provider() -> EmbeddingProvider:
    """Factory returning the active EmbeddingProvider instance (cache-wrapped)."""
    global _CACHED_PROVIDER
    if _CACHED_PROVIDER is not None:
        return _CACHED_PROVIDER

    provider_type = getattr(
        settings, "EMBEDDING_PROVIDER", os.getenv("EMBEDDING_PROVIDER", "auto")
    ).lower()
    openai_key = getattr(settings, "OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

    if provider_type == "openai" or (provider_type == "auto" and openai_key):
        inner: EmbeddingProvider = OpenAIEmbeddingProvider(api_key=openai_key)
    else:
        inner = DeterministicEmbeddingProvider()

    _CACHED_PROVIDER = CachedEmbeddingProvider(inner)
    return _CACHED_PROVIDER


def reset_embedding_provider():
    """Resets the cached provider instance (useful for unit tests)."""
    global _CACHED_PROVIDER
    _CACHED_PROVIDER = None


__all__ = [
    "EmbeddingProvider",
    "CachedEmbeddingProvider",
    "DeterministicEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "get_embedding_provider",
    "reset_embedding_provider",
]
