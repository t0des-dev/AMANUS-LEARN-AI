from rest_framework import serializers

from apps.documents.models import Document, DocumentStatus
from apps.ingestion.models import DocumentChunk, DocumentPage


class DocumentPageSerializer(serializers.ModelSerializer):
    """Serializer for extracted DocumentPage records."""

    class Meta:
        model = DocumentPage
        fields = (
            "id",
            "document",
            "page_number",
            "text",
            "ocr_used",
            "metadata",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for processed DocumentChunk records."""

    class Meta:
        model = DocumentChunk
        fields = (
            "id",
            "document",
            "page",
            "chunk_index",
            "content",
            "token_count",
            "metadata",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class DocumentProcessingStatusSerializer(serializers.ModelSerializer):
    """Serializer reporting real-time ingestion lifecycle progression."""

    progress_stage = serializers.SerializerMethodField()
    pages_count = serializers.SerializerMethodField()
    chunks_count = serializers.SerializerMethodField()
    quality_grade = serializers.SerializerMethodField()
    quality_warnings = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "status",
            "progress_stage",
            "quality_grade",
            "quality_warnings",
            "page_count",
            "pages_count",
            "chunks_count",
            "error_message",
            "updated_at",
        )
        read_only_fields = fields

    def get_quality_grade(self, obj: Document) -> str:
        meta = obj.processing_metadata or {}
        if meta.get("quality_grade"):
            return meta["quality_grade"]
        if obj.status == DocumentStatus.READY:
            return "FULL"
        if obj.status == DocumentStatus.FAILED:
            return "UNUSABLE"
        return "UNKNOWN"

    def get_quality_warnings(self, obj: Document) -> list:
        meta = obj.processing_metadata or {}
        return meta.get("quality_warnings", [])

    def get_progress_stage(self, obj: Document) -> str:
        # Check explicit stage in processing_metadata first
        meta = obj.processing_metadata or {}
        if meta.get("progress_stage"):
            return meta["progress_stage"]

        stage_mapping = {
            DocumentStatus.UPLOADING: "Uploading",
            DocumentStatus.UPLOADED: "Uploading",
            DocumentStatus.EXTRACTING: "Extracting",
            DocumentStatus.OCR: "OCR",
            DocumentStatus.STRUCTURING: "Structuring",
            DocumentStatus.CHUNKING: "Chunking",
            DocumentStatus.PROCESSING: "Extracting",
            DocumentStatus.COMPLETED: "Completed",
            DocumentStatus.READY: "Completed",
            DocumentStatus.FAILED: "Failed",
            DocumentStatus.ARCHIVED: "Archived",
        }
        return stage_mapping.get(obj.status, str(obj.status))

    def get_pages_count(self, obj: Document) -> int:
        return obj.pages.count()

    def get_chunks_count(self, obj: Document) -> int:
        return obj.chunks.count()
