import json
import logging
import os
import urllib.error
import urllib.request

from django.conf import settings

from .base import BaseTTSProvider, TTSAudioResult, TTSProviderError, TTSVoice
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
        TTSVoice(
            id="pNInz6obpgDQGcFmaJgB",
            name="Adam (ElevenLabs - عربي)",
            language="ar",
            gender="male",
            provider="elevenlabs",
            description="Voix masculine profonde et naturelle en arabe.",
        ),
    ]

    def __init__(self, api_key: str | None = None):
        self.api_key = (
            api_key
            if api_key is not None
            else getattr(settings, "ELEVENLABS_API_KEY", "") or os.getenv("ELEVENLABS_API_KEY", "")
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
            logger.info("[ElevenLabsTTSProvider] No API key; using Mock provider fallback.")
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

        max_attempts = 2
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=30) as resp:
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
            except urllib.error.HTTPError as http_err:
                last_error = http_err
                if http_err.code in (429, 502, 503, 504) and attempt < max_attempts:
                    logger.warning(
                        "[ElevenLabsTTSProvider] HTTP %d on attempt %d; retrying...",
                        http_err.code,
                        attempt,
                    )
                    continue
                logger.error("[ElevenLabsTTSProvider] HTTP %d: %s", http_err.code, http_err.reason)
                raise TTSProviderError(
                    f"Erreur ElevenLabs TTS ({http_err.code}): {http_err.reason}"
                ) from http_err
            except (urllib.error.URLError, TimeoutError) as net_err:
                last_error = net_err
                if attempt < max_attempts:
                    logger.warning(
                        "[ElevenLabsTTSProvider] Network error on attempt %d; retrying...", attempt
                    )
                    continue
                logger.error("[ElevenLabsTTSProvider] Network failure: %s", net_err)
                raise TTSProviderError(f"Échec de connexion ElevenLabs TTS: {net_err}") from net_err
            except Exception as exc:
                logger.error("[ElevenLabsTTSProvider] Unexpected error: %s", exc)
                raise TTSProviderError(f"Erreur inattendue ElevenLabs TTS: {exc}") from exc

        raise TTSProviderError(
            f"ElevenLabs TTS a échoué après {max_attempts} tentatives: {last_error}"
        )
