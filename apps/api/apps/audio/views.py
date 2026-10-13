import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import CourseSection
from apps.documents.services.storage import get_storage_service
from apps.organizations.models import RoleChoices

from .models import AudioContent, AudioStatus
from .permissions import CanManageAudio, IsAudioOrganizationMember
from .serializers import (
    AudioContentSerializer,
    AudioGenerateRequestSerializer,
)
from .services.providers import list_available_voices
from .tasks import generate_section_audio_task

logger = logging.getLogger(__name__)


class SectionAudioView(APIView):
    """POST /api/v1/sections/{id}/audio — Trigger asynchronous TTS audio generation for a section.

    GET  /api/v1/sections/{id}/audio — Retrieve existing audio content for a section.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        section = get_object_or_404(
            CourseSection.objects.select_related("course__organization"),
            id=id,
        )
        course = section.course
        organization = course.organization

        if not organization.is_member(request.user):
            raise PermissionDenied("Vous n'appartenez pas à l'organisation de ce cours.")

        user_role = organization.get_user_role(request.user)
        is_allowed = (
            user_role in (RoleChoices.OWNER, RoleChoices.ADMIN, RoleChoices.TEACHER)
            or course.created_by == request.user
        )
        if not is_allowed:
            raise PermissionDenied("Vous n'avez pas la permission de générer des contenus audio.")

        serializer = AudioGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        voice_provider = serializer.validated_data.get("voice_provider", "mock")
        voice_id = serializer.validated_data.get("voice_id", "alloy")
        language = serializer.validated_data.get("language", "fr")
        custom_script = serializer.validated_data.get("custom_script", "")

        # Look for existing audio record for this section or create new
        audio_content = AudioContent.objects.filter(section=section).first()
        if audio_content and audio_content.status == AudioStatus.PROCESSING:
            return Response(
                {
                    "detail": "Une génération audio est déjà en cours pour cette section.",
                    "code": "audio_generation_in_progress",
                    "audio": AudioContentSerializer(audio_content).data,
                },
                status=status.HTTP_409_CONFLICT,
            )

        if audio_content:
            audio_content.voice_provider = voice_provider
            audio_content.voice_id = voice_id
            audio_content.language = language
            audio_content.script = custom_script
            audio_content.status = AudioStatus.PENDING
            audio_content.error_message = ""
            audio_content.save()
        else:
            audio_content = AudioContent.objects.create(
                course=course,
                section=section,
                voice_provider=voice_provider,
                voice_id=voice_id,
                language=language,
                script=custom_script,
                status=AudioStatus.PENDING,
            )

        from apps.billing.models import UsageMetric
        from apps.billing.services.quota_service import QuotaService

        reservation = QuotaService.reserve_quota(
            organization=course.organization,
            metric=UsageMetric.AUDIO_MINUTES,
            amount=1,
            user=request.user,
            idempotency_key=f"audio_gen_{section.id}_{custom_script[:15] if custom_script else 'default'}",
            estimated_cost_usd=0.015,
        )

        try:
            # Trigger Celery asynchronous generation
            task = generate_section_audio_task.delay(str(audio_content.id))
            reservation.task_id = str(task.id)
            reservation.save(update_fields=["task_id"])
        except Exception as exc:
            QuotaService.release_quota(reservation.id, reason=str(exc))
            raise

        response_data = AudioContentSerializer(audio_content).data
        response_data["reservation_id"] = str(reservation.id)

        return Response(
            response_data,
            status=status.HTTP_202_ACCEPTED,
        )

    def get(self, request, id):
        section = get_object_or_404(
            CourseSection.objects.select_related("course__organization"),
            id=id,
        )
        if not section.course.organization.is_member(request.user):
            raise PermissionDenied("Accès interdit à cette section.")

        audio_content = (
            AudioContent.objects.filter(section=section).select_related("course", "section").first()
        )
        if not audio_content:
            return Response(
                {
                    "id": None,
                    "section_id": str(section.id),
                    "status": "NONE",
                    "detail": "Aucun contenu audio disponible pour cette section.",
                    "audio_url": None,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            AudioContentSerializer(audio_content).data,
            status=status.HTTP_200_OK,
        )


class AudioDetailView(APIView):
    """GET    /api/v1/audio/{id} — Retrieve status, duration, script, and audio_url.

    DELETE /api/v1/audio/{id} — Delete audio record and remove audio file from storage.
    """

    permission_classes = [IsAuthenticated, IsAudioOrganizationMember]

    def get(self, request, id):
        audio_content = get_object_or_404(
            AudioContent.objects.select_related("course__organization", "section"),
            id=id,
        )
        self.check_object_permissions(request, audio_content)

        return Response(
            AudioContentSerializer(audio_content).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, id):
        audio_content = get_object_or_404(
            AudioContent.objects.select_related("course__organization", "section"),
            id=id,
        )
        # Verify management permission
        perm = CanManageAudio()
        if not perm.has_object_permission(request, self, audio_content):
            raise PermissionDenied("Permission insuffisante pour supprimer cet audio.")

        # Remove physical file from storage if present
        if audio_content.storage_key:
            try:
                storage = get_storage_service()
                storage.delete_file(audio_content.storage_key)
            except Exception as e:
                logger.warning(f"Could not delete storage file {audio_content.storage_key}: {e}")

        audio_content.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VoicesListView(APIView):
    """GET /api/v1/audio/voices — List available voices for VoiceSelector."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        language = request.query_params.get("language")
        voices = list_available_voices(language=language)
        return Response({"voices": voices}, status=status.HTTP_200_OK)


class PodcastEpisodeListCreateView(APIView):
    """GET  /api/v1/audio/podcasts/ - List user's organization podcast episodes.

    POST /api/v1/audio/podcasts/ - Generate a dynamic 2-voice educational podcast episode.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import PodcastEpisode
        from .serializers import PodcastEpisodeSerializer

        qs = (
            PodcastEpisode.objects.filter(organization__members__user=request.user)
            .select_related("organization", "document", "course")
            .order_by("-created_at")
        )
        doc_id = request.query_params.get("document_id")
        course_id = request.query_params.get("course_id")
        if doc_id:
            qs = qs.filter(document_id=doc_id)
        if course_id:
            qs = qs.filter(course_id=course_id)

        serializer = PodcastEpisodeSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        from apps.ai.services import AIService, InsufficientContextError
        from apps.courses.models import Course
        from apps.documents.models import Document

        from .models import AudioStatus, PodcastEpisode
        from .serializers import (
            PodcastEpisodeSerializer,
            PodcastGenerateRequestSerializer,
        )

        serializer = PodcastGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        doc_id = data.get("document_id")
        course_id = data.get("course_id")

        if not doc_id and not course_id:
            return Response(
                {"detail": "Vous devez spécifier soit document_id soit course_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        document = None
        course = None
        organization = None

        if doc_id:
            document = get_object_or_404(Document, id=doc_id)
            if not document.organization.is_member(request.user):
                raise PermissionDenied("Vous n'êtes pas membre de cette organisation.")
            organization = document.organization

        if course_id:
            course = get_object_or_404(Course, id=course_id)
            if not course.organization.is_member(request.user):
                raise PermissionDenied("Vous n'êtes pas membre de cette organisation.")
            organization = course.organization
            if not document and course.document:
                document = course.document

        language = data.get("language") or (document.detected_language if document else "fr") or "fr"
        level = data.get("level", "BEGINNER")
        focus = data.get("focus", "")
        provider_name = data.get("voice_provider", "mock")

        ai_service = AIService()
        try:
            if document:
                generation_record = ai_service.generate_podcast_script(
                    document=document,
                    user=request.user,
                    provider_name=provider_name,
                    language=language,
                    level=level,
                    focus=focus,
                )
                dialogue_data = generation_record.result or {}
            else:
                dialogue_data = {
                    "title": f"Podcast : {course.title}",
                    "description": course.description or "Exploration audio du cours.",
                    "hosts": [
                        {"name": "Camille", "role": "host", "voice_id": "shimmer"},
                        {"name": "Alex", "role": "expert", "voice_id": "onyx"},
                    ],
                    "turns": [
                        {
                            "speaker": "Camille",
                            "role": "host",
                            "text": f"Bonjour et bienvenue ! Aujourd'hui nous décryptons le cours : {course.title}.",
                        },
                        {
                            "speaker": "Alex",
                            "role": "expert",
                            "text": "Salut Camille ! Un sujet particulièrement stimulant qui structure des concepts essentiels.",
                        },
                    ],
                    "key_takeaways": ["Principes fondamentaux du module", "Pratique méthodique"],
                    "estimated_duration_minutes": 3,
                }
        except InsufficientContextError as exc:
            return Response(
                {"detail": str(exc), "code": "insufficient_context"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("Podcast generation failed: %s", exc)
            return Response(
                {"detail": f"Erreur lors de la génération du podcast : {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        episode = PodcastEpisode.objects.create(
            organization=organization,
            document=document,
            course=course,
            title=dialogue_data.get("title") or f"Podcast - {document.title if document else course.title}",
            description=dialogue_data.get("description", ""),
            language=language,
            hosts=dialogue_data.get("hosts", []),
            turns=dialogue_data.get("turns", []),
            key_takeaways=dialogue_data.get("key_takeaways", []),
            duration=float(dialogue_data.get("estimated_duration_minutes", 4)) * 60.0,
            status=AudioStatus.COMPLETED,
            created_by=request.user,
        )

        return Response(
            PodcastEpisodeSerializer(episode).data,
            status=status.HTTP_201_CREATED,
        )


class PodcastEpisodeDetailView(APIView):
    """GET    /api/v1/audio/podcasts/<id>/ - Retrieve episode with full dialogue turns.

    DELETE /api/v1/audio/podcasts/<id>/ - Delete episode.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        from .models import PodcastEpisode
        from .serializers import PodcastEpisodeSerializer

        episode = get_object_or_404(
            PodcastEpisode.objects.filter(organization__members__user=request.user)
            .select_related("organization", "document", "course"),
            id=id,
        )
        return Response(PodcastEpisodeSerializer(episode).data, status=status.HTTP_200_OK)

    def delete(self, request, id):
        from .models import PodcastEpisode

        episode = get_object_or_404(
            PodcastEpisode.objects.filter(organization__members__user=request.user),
            id=id,
        )
        episode.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
