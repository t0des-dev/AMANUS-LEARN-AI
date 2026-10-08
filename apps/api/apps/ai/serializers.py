from rest_framework import serializers

from .models import AIGeneration


class RAGSearchRequestSerializer(serializers.Serializer):
    """Payload for RAG vector search and retrieval."""

    query = serializers.CharField(
        required=True,
        min_length=2,
        max_length=2000,
        help_text="Question ou mot-clé de recherche sémantique",
    )
    organization_id = serializers.UUIDField(
        required=True,
        help_text="UUID de l'organisation pour garantir l'isolation des données",
    )
    document_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text="Filtrer optionnellement sur un document précis",
    )
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=50,
        help_text="Nombre maximum de sources retournées",
    )


class RAGSearchResultItemSerializer(serializers.Serializer):
    """Schema for individual retrieved source chunk."""

    chunk_id = serializers.CharField()
    document_id = serializers.CharField()
    document_title = serializers.CharField()
    page = serializers.IntegerField(allow_null=True)
    page_number = serializers.IntegerField(allow_null=True)
    chapter = serializers.CharField(allow_null=True)
    section = serializers.CharField(allow_null=True)
    subsection = serializers.CharField(allow_null=True)
    chunk_index = serializers.IntegerField()
    content = serializers.CharField()
    score = serializers.FloatField()
    distance = serializers.FloatField(required=False)
    metadata = serializers.DictField(required=False)


class RAGCitationItemSerializer(serializers.Serializer):
    """Schema for structured citation provenance."""

    citation_id = serializers.IntegerField()
    chunk_id = serializers.CharField()
    document_id = serializers.CharField()
    document_title = serializers.CharField()
    page = serializers.IntegerField(allow_null=True)
    page_number = serializers.IntegerField(allow_null=True)
    chapter = serializers.CharField(allow_null=True)
    section = serializers.CharField(allow_null=True)
    subsection = serializers.CharField(allow_null=True)
    snippet = serializers.CharField()
    score = serializers.FloatField()


class RAGSearchResponseSerializer(serializers.Serializer):
    """Response returned by POST /api/v1/rag/search/."""

    query = serializers.CharField()
    organization_id = serializers.CharField()
    document_id = serializers.CharField(allow_null=True, required=False)
    count = serializers.IntegerField()
    results = RAGSearchResultItemSerializer(many=True)


class RAGQueryResponseSerializer(serializers.Serializer):
    """Response returned by POST /api/v1/rag/query/."""

    query = serializers.CharField()
    organization_id = serializers.CharField()
    document_id = serializers.CharField(allow_null=True, required=False)
    count = serializers.IntegerField()
    results = RAGSearchResultItemSerializer(many=True)
    citations = RAGCitationItemSerializer(many=True)
    context = serializers.CharField()
    sources_summary = serializers.CharField()


class GenerateRequestSerializer(serializers.Serializer):
    """Optional configuration payload for AI generation endpoints."""

    provider = serializers.CharField(
        required=False,
        default=None,
        allow_null=True,
        help_text="Fournisseur IA (openai, anthropic, gemini, local, mock, auto)",
    )
    model = serializers.CharField(
        required=False,
        default=None,
        allow_null=True,
        help_text="Modèle spécifique à utiliser",
    )
    focus = serializers.CharField(
        required=False,
        default=None,
        allow_null=True,
        allow_blank=True,
        help_text="Orientation ou question spécifique pour guider la génération",
    )
    top_k = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=20,
        help_text="Nombre de segments documentaires pertinents à inclure dans le contexte",
    )


class AIGenerationSerializer(serializers.ModelSerializer):
    """Full serialization for AIGeneration audit records."""

    class Meta:
        model = AIGeneration
        fields = [
            "id",
            "organization",
            "user",
            "document",
            "type",
            "provider",
            "model",
            "prompt_version",
            "input_tokens",
            "output_tokens",
            "status",
            "result",
            "error",
            "created_at",
        ]
        read_only_fields = fields
