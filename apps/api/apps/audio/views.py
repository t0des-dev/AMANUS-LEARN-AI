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
    VoiceSerializer,
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

        # Trigger Celery asynchronous generation
        generate_section_audio_task.delay(str(audio_content.id))

        return Response(
            AudioContentSerializer(audio_content).data,
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
            AudioContent.objects.filter(section=section)
            .select_related("course", "section")
            .first()
        )
        if not audio_content:
            return Response(
                {"detail": "Aucun contenu audio disponible pour cette section."},
                status=status.HTTP_404_NOT_FOUND,
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
                logger.warning(
                    f"Could not delete storage file {audio_content.storage_key}: {e}"
                )

        audio_content.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class VoicesListView(APIView):
    """GET /api/v1/audio/voices — List available voices for VoiceSelector."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        language = request.query_params.get("language")
        voices = list_available_voices(language=language)
        return Response({"voices": voices}, status=status.HTTP_200_OK)
