import logging

from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.models import Organization

from .models import ChatSession
from .permissions import IsSessionOwnerOrOrgAdmin
from .serializers import (
    ChatMessageCreateSerializer,
    ChatMessageSerializer,
    ChatSessionCreateSerializer,
    ChatSessionDetailSerializer,
    ChatSessionListSerializer,
)
from .services import PEDAGOGICAL_COMMANDS, AITutorService

logger = logging.getLogger(__name__)


class ChatSessionListCreateView(generics.ListCreateAPIView):
    """GET  /api/v1/chat/sessions — List conversations accessible to the user.

    POST /api/v1/chat/sessions — Create a new conversation session.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ChatSessionCreateSerializer
        return ChatSessionListSerializer

    def get_queryset(self):
        user = self.request.user
        qs = (
            ChatSession.objects.filter(
                user=user,
                organization__members__user=user,
            )
            .select_related("organization", "document", "course")
            .prefetch_related("messages")
        )

        org_id = self.request.query_params.get("organization_id")
        if org_id:
            if not Organization.objects.filter(id=org_id, members__user=user).exists():
                raise PermissionDenied("Vous n'avez pas accès aux conversations de cette organisation.")
            qs = qs.filter(organization_id=org_id)

        doc_id = self.request.query_params.get("document_id")
        if doc_id:
            qs = qs.filter(document_id=doc_id)

        return qs


class ChatSessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/v1/chat/sessions/{id} — Retrieve session details and messages.

    PATCH  /api/v1/chat/sessions/{id} — Update session title or scope.
    DELETE /api/v1/chat/sessions/{id} — Delete conversation.
    """

    permission_classes = [IsAuthenticated, IsSessionOwnerOrOrgAdmin]
    lookup_field = "id"
    lookup_url_kwarg = "id"
    serializer_class = ChatSessionDetailSerializer

    def get_queryset(self):
        user = self.request.user
        return (
            ChatSession.objects.filter(organization__members__user=user)
            .select_related("organization", "document", "course")
            .prefetch_related("messages")
        )


class ChatMessageCreateView(APIView):
    """POST /api/v1/chat/sessions/{id}/messages — Send a pedagogical question.

    Supports both standard JSON response and real-time Server-Sent Events (SSE) streaming.
    """

    permission_classes = [IsAuthenticated, IsSessionOwnerOrOrgAdmin]

    def post(self, request, id):
        session = get_object_or_404(
            ChatSession.objects.filter(
                organization__members__user=request.user
            ).select_related("organization", "document"),
            id=id,
        )
        self.check_object_permissions(request, session)

        serializer = ChatMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        content = serializer.validated_data["content"]
        command = serializer.validated_data.get("command")
        document_id = serializer.validated_data.get("document_id")
        is_stream = (
            serializer.validated_data.get("stream", False)
            or request.query_params.get("stream", "").lower() in ("1", "true")
        )

        tutor = AITutorService()

        if is_stream:
            stream_gen = tutor.process_message_stream(
                session=session,
                user_content=content,
                explicit_command=command,
                document_id=str(document_id) if document_id else None,
            )
            response = StreamingHttpResponse(
                stream_gen,
                content_type="text/event-stream; charset=utf-8",
            )
            response["Cache-Control"] = "no-cache"
            response["X-Accel-Buffering"] = "no"
            return response

        # Non-streaming synchronous response
        user_msg, assistant_msg = tutor.process_message_sync(
            session=session,
            user_content=content,
            explicit_command=command,
            document_id=str(document_id) if document_id else None,
        )

        return Response(
            {
                "session_id": str(session.id),
                "user_message": ChatMessageSerializer(user_msg).data,
                "assistant_message": ChatMessageSerializer(assistant_msg).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PedagogicalCommandsListView(APIView):
    """GET /api/v1/chat/commands — List available pedagogical commands."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        commands = [
            {
                "code": cmd.code,
                "label": cmd.label,
                "description": cmd.description,
            }
            for cmd in PEDAGOGICAL_COMMANDS.values()
        ]
        return Response({"commands": commands}, status=status.HTTP_200_OK)
