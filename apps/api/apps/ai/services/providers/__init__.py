import os

from django.conf import settings

from .anthropic_provider import AnthropicProvider
from .base import AIProvider, AIProviderError, AIResponse
from .gemini_provider import GeminiProvider
from .local_llm_provider import LocalLLMProvider
from .mock_provider import MockAIProvider
from .openai_provider import OpenAIProvider


def get_ai_provider(provider_name: str | None = None) -> AIProvider:
    """Factory returning the requested or default AIProvider instance."""
    name = (
        provider_name
        or getattr(settings, "DEFAULT_AI_PROVIDER", os.getenv("DEFAULT_AI_PROVIDER", "auto"))
    ).lower()

    if name == "mock":
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
            return MockAIProvider()
    else:
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
