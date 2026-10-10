import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

from .base import BaseTTSProvider, TTSAudioResult, TTSProviderError, TTSVoice
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
        self.api_key = api_key if api_key is not None else getattr(settings, "OPENAI_API_KEY", "")
        self._fallback = MockTTSProvider()

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        language: str = "fr",
    ) -> TTSAudioResult:
        active_voice = voice_id or self.default_voice

        if not self.api_key:
            logger.info("[OpenAITTSProvider] No API key configured; using Mock provider fallback.")
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

        max_attempts = 2
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    audio_bytes = resp.read()

                    # Approximate duration based on speech rate (~130 wpm)
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
                # Transient 429 or 5xx: retry once
                if http_err.code in (429, 502, 503, 504) and attempt < max_attempts:
                    logger.warning(
                        "[OpenAITTSProvider] HTTP %d on attempt %d; retrying...",
                        http_err.code,
                        attempt,
                    )
                    continue
                logger.error("[OpenAITTSProvider] HTTP %d: %s", http_err.code, http_err.reason)
                raise TTSProviderError(
                    f"Erreur OpenAI TTS ({http_err.code}): {http_err.reason}"
                ) from http_err
            except (urllib.error.URLError, TimeoutError) as net_err:
                last_error = net_err
                if attempt < max_attempts:
                    logger.warning(
                        "[OpenAITTSProvider] Network error on attempt %d; retrying...", attempt
                    )
                    continue
                logger.error("[OpenAITTSProvider] Network failure: %s", net_err)
                raise TTSProviderError(f"Échec de connexion OpenAI TTS: {net_err}") from net_err
            except Exception as exc:
                logger.error("[OpenAITTSProvider] Unexpected error: %s", exc)
                raise TTSProviderError(f"Erreur inattendue OpenAI TTS: {exc}") from exc

        raise TTSProviderError(f"OpenAI TTS a échoué après {max_attempts} tentatives: {last_error}")
