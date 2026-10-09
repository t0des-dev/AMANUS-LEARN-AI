from .base import BaseTTSProvider, TTSAudioResult, TTSVoice


class MockTTSProvider(BaseTTSProvider):
    """Deterministic Mock TTS Provider for unit testing and offline development."""

    name: str = "mock"
    default_voice: str = "pierre"

    _VOICES: list[TTSVoice] = [
        TTSVoice(
            id="pierre",
            name="Pierre",
            language="fr",
            gender="male",
            provider="mock",
            description="Voix masculine posée, claire et académique.",
        ),
        TTSVoice(
            id="marie",
            name="Marie",
            language="fr",
            gender="female",
            provider="mock",
            description="Voix féminine dynamique, chaleureuse et pédagogique.",
        ),
        TTSVoice(
            id="clara",
            name="Clara",
            language="fr",
            gender="female",
            provider="mock",
            description="Voix féminine douce, idéale pour les révisions calmes.",
        ),
        TTSVoice(
            id="antoine",
            name="Antoine",
            language="fr",
            gender="male",
            provider="mock",
            description="Voix masculine énergique et engageante.",
        ),
        TTSVoice(
            id="adam",
            name="Adam",
            language="en",
            gender="male",
            provider="mock",
            description="English male narrator, articulate and balanced.",
        ),
        TTSVoice(
            id="rachel",
            name="Rachel",
            language="en",
            gender="female",
            provider="mock",
            description="English female speaker, professional and clear.",
        ),
        TTSVoice(
            id="tariq",
            name="Tariq (طارق)",
            language="ar",
            gender="male",
            provider="mock",
            description="Voix masculine arabe claire, éloquente et académique.",
        ),
        TTSVoice(
            id="layla",
            name="Layla (ليلى)",
            language="ar",
            gender="female",
            provider="mock",
            description="Voix féminine arabe douce, dynamique et pédagogique.",
        ),
        TTSVoice(
            id="omar",
            name="Omar (عمر)",
            language="ar",
            gender="male",
            provider="mock",
            description="Voix masculine arabe posée et chaleureuse pour les cours.",
        ),
        TTSVoice(
            id="fatima",
            name="Fatima (فاطمة)",
            language="ar",
            gender="female",
            provider="mock",
            description="Voix féminine arabe claire, professionnelle et articulée.",
        ),
    ]

    def synthesize(
        self,
        text: str,
        voice_id: str | None = None,
        language: str = "fr",
    ) -> TTSAudioResult:
        active_voice = voice_id or self.default_voice
        word_count = max(1, len(text.strip().split()))

        # Average pedagogical speech rate: ~130 words/min ≈ 2.17 words/sec
        estimated_duration = max(1.5, round(word_count / 2.17, 1))

        # Generate a standard valid MP3 byte stream with MPEG-1 Audio Layer 3 sync header
        # ID3v2 header: 'ID3' + version (3.0) + flags (0) + size (10 bytes)
        id3_header = b"ID3\x03\x00\x00\x00\x00\x00\x00"
        # Standard MPEG 1 Layer 3 128kbps 44.1kHz stereo sync word: 0xFF 0xFB 0x90 0x64
        mp3_frame = b"\xff\xfb\x90\x64" + (b"\x00" * 413)
        # Repeat frames according to estimated duration (approx 26 frames per second in mp3)
        frames_count = max(5, int(estimated_duration * 10))
        audio_bytes = id3_header + (mp3_frame * frames_count)

        return TTSAudioResult(
            audio_bytes=audio_bytes,
            duration=estimated_duration,
            format="mp3",
            voice_id=active_voice,
            provider=self.name,
        )
