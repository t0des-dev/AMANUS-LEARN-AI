from rest_framework import serializers

from apps.courses.models import Course
from apps.documents.models import Document
from apps.organizations.models import Organization

from .models import ChatMessage, ChatSession


class DocumentBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ("id", "title", "file_type", "status")


class CourseBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ("id", "title", "level", "status")


class ChatMessageSerializer(serializers.ModelSerializer):
    session_id = serializers.UUIDField(source="session.id", read_only=True)
    sender = serializers.CharField(source="role", read_only=True)

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "session_id",
            "role",
            "sender",
            "content",
            "command",
            "sources",
            "tokens_used",
            "metadata",
            "created_at",
        )
        read_only_fields = ("id", "session_id", "created_at", "sources", "tokens_used", "metadata")


class ChatMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_blank=False)
    message = serializers.CharField(required=False, allow_blank=False)
    command = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    stream = serializers.BooleanField(required=False, default=False)
    document_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, attrs):
        # Support both 'content' and 'message' keys
        text = attrs.get("content") or attrs.get("message")
        if not text or not text.strip():
            raise serializers.ValidationError(
                {"content": "Le contenu du message ne peut pas être vide."}
            )
        attrs["content"] = text.strip()
        return attrs


class ChatSessionListSerializer(serializers.ModelSerializer):
    document = DocumentBriefSerializer(read_only=True)
    course = CourseBriefSerializer(read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = (
            "id",
            "title",
            "organization_id",
            "user_id",
            "document",
            "course",
            "message_count",
            "last_message",
            "created_at",
            "updated_at",
        )

    def get_message_count(self, obj: ChatSession) -> int:
        return obj.messages.count()

    def get_last_message(self, obj: ChatSession) -> dict | None:
        last = obj.messages.order_by("-created_at").first()
        if not last:
            return None
        return {
            "id": str(last.id),
            "role": last.role,
            "content": last.content[:100] + ("..." if len(last.content) > 100 else ""),
            "created_at": last.created_at.isoformat(),
        }


class ChatSessionDetailSerializer(serializers.ModelSerializer):
    document = DocumentBriefSerializer(read_only=True)
    course = CourseBriefSerializer(read_only=True)
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = (
            "id",
            "title",
            "organization_id",
            "user_id",
            "document",
            "course",
            "messages",
            "created_at",
            "updated_at",
        )


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(required=False)
    document_id = serializers.UUIDField(required=False, allow_null=True)
    course_id = serializers.UUIDField(required=False, allow_null=True)
    initial_message = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = ChatSession
        fields = (
            "id",
            "title",
            "organization_id",
            "document_id",
            "course_id",
            "initial_message",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        user = self.context["request"].user
        org_id = attrs.get("organization_id")

        if org_id:
            if not Organization.objects.filter(id=org_id, members__user=user).exists():
                raise serializers.ValidationError(
                    {"organization_id": "Organisation invalide ou accès non autorisé."}
                )
        else:
            # Fall back to user's first organization
            membership = user.organization_memberships.first()
            if not membership:
                raise serializers.ValidationError(
                    {"organization_id": "Vous devez appartenir à au moins une organisation."}
                )
            attrs["organization_id"] = membership.organization_id

        doc_id = attrs.get("document_id")
        if doc_id:
            if not Document.objects.filter(
                id=doc_id, organization_id=attrs["organization_id"]
            ).exists():
                raise serializers.ValidationError(
                    {"document_id": "Document introuvable dans cette organisation."}
                )

        course_id = attrs.get("course_id")
        if course_id:
            if not Course.objects.filter(
                id=course_id, organization_id=attrs["organization_id"]
            ).exists():
                raise serializers.ValidationError(
                    {"course_id": "Cours introuvable dans cette organisation."}
                )

        return attrs

    def create(self, validated_data):
        initial_message = validated_data.pop("initial_message", None)
        user = self.context["request"].user
        session = ChatSession.objects.create(user=user, **validated_data)

        if initial_message and initial_message.strip():
            from .services import AITutorService

            tutor = AITutorService()
            tutor.process_message_sync(session=session, user_content=initial_message.strip())

        return session


class PedagogicalCommandSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
