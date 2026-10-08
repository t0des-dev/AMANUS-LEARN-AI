from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import NamedTuple


class TTSVoice(NamedTuple):
    """Voice metadata for text-to-speech synthesis."""

    id: str
    name: str
    language: str
    gender: str
    provider: str
    description: str = ""


@dataclass
class TTSAudioResult:
    """Standardized result returned by TTS providers."""

    audio_bytes: bytes
    duration: float  # In seconds
    format: str = "mp3"
    voice_id: str = ""
    provider: str = ""


class TTSProviderError(Exception):
    """Raised when text-to-speech synthesis fails."""

    pass


class BaseTTSProvider(ABC):
    """Abstract base class for all Text-To-Speech providers."""

    name: str = "base"
    default_voice: str = "default"

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        language: str = "fr",
    ) -> TTSAudioResult:
        """Synthesizes text into audio bytes and measures/estimates duration."""
        pass

    @abstractmethod
    def get_available_voices(self, language: str | None = None) -> list[TTSVoice]:
        """Returns the list of voices provided by this backend."""
        pass
