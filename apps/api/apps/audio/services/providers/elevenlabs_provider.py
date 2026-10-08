import json
import logging
import os
import urllib.error
import urllib.request

from django.conf import settings

from .base import BaseTTSProvider, TTSAudioResult, TTSVoice
from .mock_provider import MockTTSProvider

logger = logging.getLogger(__name__)


class ElevenLabsTTSProvider(BaseTTSProvider):
    """Adapter for ElevenLabs Voice API."""

    name: str = "elevenlabs"
    default_voice: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel

    _VOICES: list[TTSVoice] = [
        TTSVoice(
            id="21m00Tcm4TlvDq8ikWAM",
            name="Rachel (ElevenLabs)",
            language="en",
            gender="female",
            provider="elevenlabs",
            description="Voix féminine naturelle et professionnelle.",
        ),
        TTSVoice(
            id="AZnzlk1XvdvUeBnXmlld",
            name="Domi (ElevenLabs)",
            language="fr",
            gender="female",
            provider="elevenlabs",
            description="Voix féminine expressive et rythmée.",
        ),
        TTSVoice(
            id="EXAVITQu4vr4xnSDxMaL",
            name="Bella (ElevenLabs)",
            language="fr",
            gender="female",
            provider="elevenlabs",
            description="Voix féminine douce et didactique.",
        ),
        TTSVoice(
            id="ErXwobaYiN019PkySvjV",
            name="Antoni (ElevenLabs)",
            language="fr",
            gender="male",
            provider="elevenlabs",
            description="Voix masculine claire et modulée.",
        ),
    ]

    def __init__(self, api_key: str | None = None):
        self.api_key = (
            api_key
            or getattr(settings, "ELEVENLABS_API_KEY", "")
            or os.getenv("ELEVENLABS_API_KEY", "")
        )
        self._fallback = MockTTSProvider()

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        language: str = "fr",
    ) -> TTSAudioResult:
        active_voice = voice_id or self.default_voice

        if not self.api_key:
            logger.info("[ElevenLabsTTSProvider] No API key; falling back to Mock provider.")
            return self._fallback.synthesize(text=text, voice_id=active_voice, language=language)

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{active_voice}"
        payload_dict = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }
        payload = json.dumps(payload_dict).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "xi-api-key": self.api_key,
        }

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as resp:
                audio_bytes = resp.read()
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
            logger.warning(f"[ElevenLabsTTSProvider] Call failed ({e}); falling back to mock.")
            return self._fallback.synthesize(text=text, voice_id=active_voice, language=language)

    def get_available_voices(self, language: str | None = None) -> list[TTSVoice]:
        return list(self._VOICES)
