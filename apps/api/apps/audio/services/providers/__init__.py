import os
from typing import Any

from django.conf import settings

from .base import BaseTTSProvider, TTSAudioResult, TTSProviderError, TTSVoice
from .elevenlabs_provider import ElevenLabsTTSProvider
from .mock_provider import MockTTSProvider
from .openai_provider import OpenAITTSProvider


def get_tts_provider(provider_name: str | None = None) -> BaseTTSProvider:
    """Factory returning the requested or default TTSProvider instance."""
    name = (
        provider_name
        or getattr(settings, "DEFAULT_TTS_PROVIDER", os.getenv("DEFAULT_TTS_PROVIDER", "auto"))
    ).lower()

    if name == "mock":
        return MockTTSProvider()
    elif name == "openai":
        return OpenAITTSProvider()
    elif name == "elevenlabs":
        return ElevenLabsTTSProvider()
    elif name == "auto":
        if getattr(settings, "OPENAI_API_KEY", os.getenv("OPENAI_API_KEY")):
            return OpenAITTSProvider()
        elif getattr(settings, "ELEVENLABS_API_KEY", os.getenv("ELEVENLABS_API_KEY")):
            return ElevenLabsTTSProvider()
        else:
            return MockTTSProvider()
    else:
        return MockTTSProvider()


def list_available_voices(language: str | None = None) -> list[dict[str, Any]]:
    """Aggregates voices from all supported providers."""
    providers: list[BaseTTSProvider] = [
        MockTTSProvider(),
        OpenAITTSProvider(),
        ElevenLabsTTSProvider(),
    ]

    seen = set()
    voices = []

    for prov in providers:
        for v in prov.get_available_voices(language=language):
            key = (v.provider, v.id)
            if key not in seen:
                seen.add(key)
                voices.append(
                    {
                        "id": v.id,
                        "name": v.name,
                        "language": v.language,
                        "gender": v.gender,
                        "provider": v.provider,
                        "description": v.description,
                    }
                )

    return voices


__all__ = [
    "BaseTTSProvider",
    "TTSAudioResult",
    "TTSVoice",
    "TTSProviderError",
    "MockTTSProvider",
    "OpenAITTSProvider",
    "ElevenLabsTTSProvider",
    "get_tts_provider",
    "list_available_voices",
]
