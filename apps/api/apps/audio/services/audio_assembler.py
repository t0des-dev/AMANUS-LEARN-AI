import logging

from .providers.base import TTSAudioResult, TTSProviderError

logger = logging.getLogger(__name__)


class AudioAssembler:
    """Validates audio byte streams and concatenates multi-segment MP3 audio chunks.

    Ensures that:
    1. Audio files start with valid audio magic headers (ID3 or MPEG-1/2 Audio Layer 3 sync word).
    2. Minimum audio size is respected (rejects empty or truncated files).
    3. Multi-segment concatenation strips redundant ID3 metadata headers from subsequent chunks
       to prevent audio artifacts and ensure seamless playback.
    """

    MIN_AUDIO_BYTES = 48
    MPEG_SYNC_BYTES = (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")

    @classmethod
    def validate_audio_bytes(cls, audio_bytes: bytes | None, min_size: int | None = None) -> bool:
        """Validates that bytes represent a non-empty, well-formed MP3 audio stream."""
        if not audio_bytes:
            raise TTSProviderError("Le flux audio généré est vide.")

        min_allowed = min_size or cls.MIN_AUDIO_BYTES
        if len(audio_bytes) < min_allowed:
            raise TTSProviderError(
                f"Le fichier audio est trop court ({len(audio_bytes)} octets, minimum requis: {min_allowed} octets)."
            )

        # Check for ID3 tag header or MPEG frame sync
        is_id3 = audio_bytes.startswith(b"ID3")
        is_mpeg_frame = any(audio_bytes.startswith(sync) for sync in cls.MPEG_SYNC_BYTES)

        if not (is_id3 or is_mpeg_frame):
            logger.warning("Audio bytes do not start with standard ID3 or MPEG sync header.")
            # We still allow files that contain sync word within first 32 bytes
            found_sync = False
            for sync in cls.MPEG_SYNC_BYTES:
                if sync in audio_bytes[:1024]:
                    found_sync = True
                    break
            if not found_sync:
                raise TTSProviderError("Format audio invalide : signature MP3 / ID3 non reconnue.")

        return True

    @classmethod
    def strip_id3_header(cls, audio_bytes: bytes) -> bytes:
        """Strips ID3v2 metadata header if present at the start of audio bytes."""
        if not audio_bytes.startswith(b"ID3") or len(audio_bytes) < 10:
            return audio_bytes

        # ID3v2 tag size is encoded as 4 synchsafe 7-bit integers in bytes 6-9
        b6, b7, b8, b9 = audio_bytes[6:10]
        tag_size = ((b6 & 0x7F) << 21) | ((b7 & 0x7F) << 14) | ((b8 & 0x7F) << 7) | (b9 & 0x7F)
        total_header_size = 10 + tag_size

        if len(audio_bytes) > total_header_size:
            return audio_bytes[total_header_size:]
        return audio_bytes

    @classmethod
    def assemble_segments(
        cls,
        segments_results: list[TTSAudioResult],
        expected_format: str = "mp3",
    ) -> TTSAudioResult:
        """Assembles multiple synthesized audio segments into a single unified TTSAudioResult."""
        if not segments_results:
            raise TTSProviderError("Aucun segment audio à assembler.")

        if len(segments_results) == 1:
            cls.validate_audio_bytes(segments_results[0].audio_bytes)
            return segments_results[0]

        assembled_bytes_parts: list[bytes] = []
        total_duration = 0.0
        voice_id = segments_results[0].voice_id
        provider = segments_results[0].provider

        for idx, res in enumerate(segments_results):
            cls.validate_audio_bytes(res.audio_bytes)
            total_duration += res.duration

            if idx == 0:
                # Keep initial container / ID3 header
                assembled_bytes_parts.append(res.audio_bytes)
            else:
                # Strip duplicate ID3 tag from subsequent segments for seamless concatenation
                pure_frames = cls.strip_id3_header(res.audio_bytes)
                assembled_bytes_parts.append(pure_frames)

        final_audio_bytes = b"".join(assembled_bytes_parts)
        cls.validate_audio_bytes(final_audio_bytes)

        return TTSAudioResult(
            audio_bytes=final_audio_bytes,
            duration=round(total_duration, 2),
            format=expected_format,
            voice_id=voice_id,
            provider=provider,
        )
