import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

from .base import BaseTTSProvider, TTSAudioResult, TTSVoice
from .mock_provider import MockTTSProvider

logger = logging.getLogger(__name__)


class OpenAITTSProvider(BaseTTSProvider):
    """Adapter for OpenAI Speech API (model tts-1)."""

    name: str = "openai"
    default_voice: str = "alloy"

    _VOICES: list[TTSVoice] = [
        TTSVoice(
            id="alloy",
            name="Alloy",
            language="fr",
            gender="neutral",
            provider="openai",
            description="Voix neutre, équilibrée et fluide.",
        ),
        TTSVoice(
            id="echo",
            name="Echo",
            language="fr",
            gender="male",
            provider="openai",
            description="Voix masculine chaleureuse et posée.",
        ),
        TTSVoice(
            id="fable",
            name="Fable",
            language="fr",
            gender="male",
            provider="openai",
            description="Voix expressive avec accent narratif.",
        ),
        TTSVoice(
            id="onyx",
            name="Onyx",
            language="fr",
            gender="male",
            provider="openai",
            description="Voix masculine grave et autoritaire.",
        ),
        TTSVoice(
            id="nova",
            name="Nova",
            language="fr",
            gender="female",
            provider="openai",
            description="Voix féminine dynamique et engageante.",
        ),
        TTSVoice(
            id="shimmer",
            name="Shimmer",
            language="fr",
            gender="female",
            provider="openai",
            description="Voix féminine claire et posée.",
        ),
        TTSVoice(
            id="alloy",
            name="Alloy (عربي)",
            language="ar",
            gender="neutral",
            provider="openai",
            description="Voix OpenAI neutre et fluide en arabe.",
        ),
        TTSVoice(
            id="nova",
            name="Nova (عربي)",
            language="ar",
            gender="female",
            provider="openai",
            description="Voix OpenAI féminine et claire en arabe.",
        ),
        TTSVoice(
            id="echo",
            name="Echo (عربي)",
            language="ar",
            gender="male",
            provider="openai",
            description="Voix OpenAI masculine et posée en arabe.",
        ),
    ]

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
        self._fallback = MockTTSProvider()

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        language: str = "fr",
    ) -> TTSAudioResult:
        active_voice = voice_id or self.default_voice

        if not self.api_key:
            logger.info("[OpenAITTSProvider] No API key; falling back to Mock provider.")
            return self._fallback.synthesize(text=text, voice_id=active_voice, language=language)

        url = "https://api.openai.com/v1/audio/speech"
        payload_dict = {
            "model": "tts-1",
            "input": text,
            "voice": active_voice,
            "response_format": "mp3",
        }
        payload = json.dumps(payload_dict).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as resp:
                audio_bytes = resp.read()

                # Approximate duration based on words
                words = len(text.strip().split())
                duration = max(1.5, round(words / 2.17, 1))

                return TTSAudioResult(
                    audio_bytes=audio_bytes,
                    duration=duration,
                    format="mp3",
                    voice_id=active_voice,
                    provider=self.name,
                )
        except Exception as e:
            logger.warning(f"[OpenAITTSProvider] OpenAI TTS failed ({e}); falling back to mock.")
            return self._fallback.synthesize(text=text, voice_id=active_voice, language=language)
