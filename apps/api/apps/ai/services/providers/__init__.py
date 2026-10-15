import os

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .anthropic_provider import AnthropicProvider
from .base import AIProvider, AIProviderError, AIResponse
from .gemini_provider import GeminiProvider
from .local_llm_provider import LocalLLMProvider
from .mock_provider import MockAIProvider
from .openai_provider import OpenAIProvider


def _mock_allowed() -> bool:
    """Mock provider is only usable when explicitly allowed.

    Defaults to allowed in DEBUG (local dev / demo) and forbidden in production
    unless `ALLOW_MOCK_AI_PROVIDER=True` is deliberately set. This prevents the
    demo fixture provider from silently serving real users in production.
    """
    if getattr(settings, "ALLOW_MOCK_AI_PROVIDER", None) is not None:
        return bool(settings.ALLOW_MOCK_AI_PROVIDER)
    return bool(getattr(settings, "DEBUG", False))


def get_ai_provider(provider_name: str | None = None) -> AIProvider:
    """Factory returning the requested or default AIProvider instance."""
    name = (
        provider_name
        or getattr(settings, "DEFAULT_AI_PROVIDER", os.getenv("DEFAULT_AI_PROVIDER", "auto"))
    ).lower()

    if name == "mock":
        if not _mock_allowed():
            raise ImproperlyConfigured(
                "Mock AI provider is disabled in this environment. "
                "Set ALLOW_MOCK_AI_PROVIDER=True explicitly if this is intentional."
            )
        return MockAIProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "gemini":
        return GeminiProvider()
    elif name == "local":
        return LocalLLMProvider()
    elif name == "auto":
        # Auto-detect available provider based on configured API keys
        if getattr(settings, "OPENAI_API_KEY", os.getenv("OPENAI_API_KEY")):
            return OpenAIProvider()
        elif getattr(settings, "ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY")):
            return AnthropicProvider()
        elif getattr(settings, "GEMINI_API_KEY", os.getenv("GEMINI_API_KEY")):
            return GeminiProvider()
        else:
            if not _mock_allowed():
                raise ImproperlyConfigured(
                    "No AI provider API key is configured and the mock fallback is disabled "
                    "in this environment. Configure OPENAI_API_KEY / ANTHROPIC_API_KEY / "
                    "GEMINI_API_KEY, or set ALLOW_MOCK_AI_PROVIDER=True for local demo use."
                )
            return MockAIProvider()
    else:
        if not _mock_allowed():
            raise ImproperlyConfigured(
                f"Unknown AI provider '{name}' and mock fallback is disabled in this environment."
            )
        return MockAIProvider()


__all__ = [
    "AIProvider",
    "AIResponse",
    "AIProviderError",
    "MockAIProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "GeminiProvider",
    "LocalLLMProvider",
    "get_ai_provider",
]
