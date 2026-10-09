import logging
import uuid

from apps.documents.services.storage import get_storage_service

from ..models import AudioContent, AudioStatus
from .providers import get_tts_provider
from .script_generator import PedagogicalScriptGenerator

logger = logging.getLogger(__name__)


class AudioPipelineService:
    """Orchestrates the Audio / TTS generation pipeline:

    Lesson -> Pedagogical Script -> TTS Synthesis -> Audio File -> Storage Persistence.
    """

    def __init__(
        self,
        script_generator: PedagogicalScriptGenerator | None = None,
        storage_service=None,
    ):
        self.script_generator = script_generator or PedagogicalScriptGenerator()
        self.storage_service = storage_service or get_storage_service()

    def process_audio_generation(self, audio_content_id: str) -> AudioContent:
        """Executes full TTS generation pipeline for an AudioContent instance."""
        try:
            audio_content = AudioContent.objects.select_related("course", "section").get(
                id=audio_content_id
            )
        except AudioContent.DoesNotExist:
            logger.error(f"[AudioPipeline] AudioContent {audio_content_id} not found.")
            raise

        audio_content.status = AudioStatus.PROCESSING
        audio_content.save(update_fields=["status", "updated_at"])

        try:
            # 1. Lesson -> Pedagogical Script
            section = audio_content.section
            if not audio_content.script or not audio_content.script.strip():
                script = self.script_generator.generate_script(section)
                audio_content.script = script
            else:
                script = audio_content.script

            # 2. Script -> TTS Synthesis
            tts_provider = get_tts_provider(audio_content.voice_provider)
            logger.info(
                f"[AudioPipeline] Synthesizing audio with {tts_provider.name} (voice={audio_content.voice_id})"
            )
            synthesis_result = tts_provider.synthesize(
                text=script,
                voice_id=audio_content.voice_id,
                language=audio_content.language,
            )

            # 3. Audio Bytes -> Storage Persistence
            course_id_str = str(audio_content.course_id)
            section_id_str = str(audio_content.section_id)
            unique_token = uuid.uuid4().hex[:8]
            storage_key = (
                f"audio/courses/{course_id_str}/sections/{section_id_str}_{unique_token}.mp3"
            )

            self.storage_service.save_file(
                storage_key=storage_key,
                content=synthesis_result.audio_bytes,
                content_type="audio/mpeg",
            )

            # 4. Finalize AudioContent
            audio_content.storage_key = storage_key
            audio_content.duration = synthesis_result.duration
            audio_content.status = AudioStatus.COMPLETED
            audio_content.error_message = ""
            audio_content.save(
                update_fields=[
                    "storage_key",
                    "duration",
                    "script",
                    "status",
                    "error_message",
                    "updated_at",
                ]
            )

            logger.info(
                f"[AudioPipeline] Audio generation completed successfully for section {section.id} (duration: {audio_content.duration}s)"
            )
            return audio_content

        except Exception as exc:
            logger.error(
                f"[AudioPipeline] TTS pipeline failed for {audio_content_id}: {exc}",
                exc_info=True,
            )
            audio_content.status = AudioStatus.FAILED
            audio_content.error_message = str(exc)
            audio_content.save(update_fields=["status", "error_message", "updated_at"])
            raise
