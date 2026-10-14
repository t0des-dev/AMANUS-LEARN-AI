import uuid
from pathlib import Path

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.organizations.models import Organization

from .models import Document, DocumentStatus
from .services.storage import get_storage_service
from .validators import validate_document_file


class DocumentListSerializer(serializers.ModelSerializer):
    """Compact serializer for document listings."""

    owner = UserSerializer(read_only=True)
    file_size_human = serializers.ReadOnlyField()
    file_extension = serializers.ReadOnlyField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "organization",
            "owner",
            "title",
            "description",
            "file_name",
            "file_type",
            "file_size",
            "file_size_human",
            "file_extension",
            "language",
            "page_count",
            "status",
            "download_url",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_download_url(self, obj: Document) -> str:
        try:
            return obj.get_download_url()
        except Exception:
            return ""


class DocumentDetailSerializer(serializers.ModelSerializer):
    """Detailed document serializer with storage key and metadata."""

    owner = UserSerializer(read_only=True)
    file_size_human = serializers.ReadOnlyField()
    file_extension = serializers.ReadOnlyField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "organization",
            "owner",
            "title",
            "description",
            "file_name",
            "file_type",
            "file_size",
            "file_size_human",
            "file_extension",
            "storage_key",
            "language",
            "page_count",
            "status",
            "error_message",
            "processing_metadata",
            "download_url",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "organization",
            "owner",
            "file_name",
            "file_type",
            "file_size",
            "file_size_human",
            "file_extension",
            "storage_key",
            "error_message",
            "processing_metadata",
            "download_url",
            "created_at",
            "updated_at",
        )

    def get_download_url(self, obj: Document) -> str:
        try:
            return obj.get_download_url()
        except Exception:
            return ""


class DocumentUploadSerializer(serializers.Serializer):
    """Multipart upload serializer with multi-tenant membership and file validation."""

    file = serializers.FileField(write_only=True, required=True)
    organization_id = serializers.UUIDField(write_only=True, required=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    language = serializers.CharField(max_length=10, required=False, default="fr")

    def validate(self, attrs):
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError({"detail": "Authentification requise."})

        org_id = attrs.get("organization_id")
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            raise serializers.ValidationError({"organization_id": "Organisation introuvable."})

        # Check tenant membership
        if not organization.is_member(request.user):
            raise serializers.ValidationError(
                {"organization_id": "Vous n'êtes pas membre de cette organisation."}
            )

        # Validate file
        uploaded_file = attrs.get("file")
        validate_document_file(uploaded_file)

        attrs["organization"] = organization
        return attrs

    def create(self, validated_data) -> Document:
        request = self.context["request"]
        uploaded_file = validated_data["file"]
        organization = validated_data["organization"]

        from .validators import sanitize_file_name

        original_name = sanitize_file_name(uploaded_file.name)
        file_ext = Path(original_name).suffix.lstrip(".").lower()
        title = validated_data.get("title")
        if not title or not title.strip():
            title = Path(original_name).stem.replace("_", " ").replace("-", " ").title()

        doc_uuid = uuid.uuid4()
        # Secure storage key isolated per organization and sanitized against path traversal
        storage_key = f"organizations/{organization.id}/documents/{doc_uuid}/{original_name}"

        # Persist to abstract storage
        storage = get_storage_service()
        content_type = getattr(uploaded_file, "content_type", "application/octet-stream")
        storage.save_file(storage_key, uploaded_file, content_type=content_type)

        document = Document.objects.create(
            id=doc_uuid,
            organization=organization,
            owner=request.user,
            title=title,
            description=validated_data.get("description", ""),
            file_name=original_name,
            file_type=file_ext,
            file_size=uploaded_file.size,
            storage_key=storage_key,
            language=validated_data.get("language", "fr"),
            status=DocumentStatus.UPLOADED,
        )
        return document


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """Allows updating document metadata."""

    class Meta:
        model = Document
        fields = ("title", "description", "language", "status")

    def validate_status(self, value):
        if value not in DocumentStatus.values:
            raise serializers.ValidationError("Statut de document invalide.")
        return value


class DocumentStatusSerializer(serializers.ModelSerializer):
    """Returns concise processing status information."""

    class Meta:
        model = Document
        fields = ("id", "status", "page_count", "created_at", "updated_at")
        read_only_fields = fields


class DocumentURLIngestSerializer(serializers.Serializer):
    """Serializer for web URL ingestion into Document model."""

    url = serializers.URLField(required=True)
    organization_id = serializers.UUIDField(required=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    language = serializers.CharField(max_length=10, required=False, default="fr")

    def validate(self, attrs):
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            raise serializers.ValidationError({"detail": "Authentification requise."})

        org_id = attrs.get("organization_id")
        try:
            organization = Organization.objects.get(id=org_id)
        except Organization.DoesNotExist:
            raise serializers.ValidationError({"organization_id": "Organisation introuvable."})

        if not organization.is_member(request.user):
            raise serializers.ValidationError(
                {"organization_id": "Vous n'êtes pas membre de cette organisation."}
            )

        attrs["organization"] = organization
        return attrs

    def create(self, validated_data) -> Document:
        import io
        import uuid

        from apps.documents.services.storage import get_storage_service
        from apps.documents.services.url_extractor import URLExtractorService

        request = self.context["request"]
        url = validated_data["url"]
        organization = validated_data["organization"]

        try:
            extracted_title, text_content = URLExtractorService.fetch_and_extract(url)
        except Exception as exc:
            raise serializers.ValidationError({"url": f"Extraction impossible : {exc}"})

        title = validated_data.get("title") or extracted_title
        doc_uuid = uuid.uuid4()
        file_name = f"web_{doc_uuid.hex[:8]}.txt"
        storage_key = f"organizations/{organization.id}/documents/{doc_uuid}/{file_name}"

        content_bytes = text_content.encode("utf-8")
        file_obj = io.BytesIO(content_bytes)
        file_obj.size = len(content_bytes)

        storage = get_storage_service()
        storage.save_file(storage_key, file_obj, content_type="text/plain; charset=utf-8")

        document = Document.objects.create(
            id=doc_uuid,
            organization=organization,
            owner=request.user,
            title=title,
            description=validated_data.get("description", "") or f"Importé depuis {url}",
            file_name=file_name,
            file_type="txt",
            file_size=len(content_bytes),
            storage_key=storage_key,
            language=validated_data.get("language", "fr"),
            status=DocumentStatus.UPLOADED,
        )
        return document

