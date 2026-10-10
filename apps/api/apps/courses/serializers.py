from rest_framework import serializers

from .models import Course, CourseLevel, CourseSection


class CourseSectionSerializer(serializers.ModelSerializer):
    """Flat serialization for a single CourseSection."""

    level_depth = serializers.IntegerField(read_only=True)

    class Meta:
        model = CourseSection
        fields = [
            "id",
            "course",
            "parent",
            "title",
            "order",
            "content",
            "summary",
            "objectives",
            "estimated_minutes",
            "level_depth",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "course", "created_at", "updated_at", "level_depth"]


class CourseSectionTreeSerializer(serializers.ModelSerializer):
    """Hierarchical recursive serialization for Course -> Chapter -> Section -> Lesson outline."""

    children = serializers.SerializerMethodField()
    level_depth = serializers.IntegerField(read_only=True)

    class Meta:
        model = CourseSection
        fields = [
            "id",
            "parent",
            "title",
            "order",
            "summary",
            "content",
            "objectives",
            "estimated_minutes",
            "level_depth",
            "children",
            "created_at",
            "updated_at",
        ]

    def get_children(self, obj: CourseSection) -> list[dict]:
        children = obj.children.all().order_by("order", "created_at")
        return CourseSectionTreeSerializer(children, many=True).data


class CourseListSerializer(serializers.ModelSerializer):
    """Summary representation for course listings."""

    sections_count = serializers.SerializerMethodField()
    total_estimated_minutes = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    creator_name = serializers.CharField(
        source="created_by.full_name", read_only=True, default=None
    )

    class Meta:
        model = Course
        fields = [
            "id",
            "organization",
            "organization_name",
            "document",
            "created_by",
            "creator_name",
            "title",
            "description",
            "language",
            "level",
            "status",
            "sections_count",
            "total_estimated_minutes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "sections_count",
            "total_estimated_minutes",
            "created_at",
            "updated_at",
        ]

    def get_sections_count(self, obj: Course) -> int:
        return obj.sections.count()

    def get_total_estimated_minutes(self, obj: Course) -> int:
        return sum(s.estimated_minutes for s in obj.sections.all())


class CourseDetailSerializer(CourseListSerializer):
    """Detailed course representation including hierarchical root sections (Chapters)."""

    sections = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ["sections"]

    def get_sections(self, obj: Course) -> list[dict]:
        # Only fetch root sections (parent=None, i.e. Chapters)
        root_sections = obj.sections.filter(parent__isnull=True).order_by("order", "created_at")
        return CourseSectionTreeSerializer(root_sections, many=True).data


class CourseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new course."""

    class Meta:
        model = Course
        fields = [
            "id",
            "organization",
            "document",
            "created_by",
            "title",
            "description",
            "language",
            "level",
            "status",
        ]
        read_only_fields = ["id", "created_by"]


class CourseUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating course metadata."""

    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "language",
            "level",
            "status",
            "document",
        ]


class CourseSectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new section under a course."""

    class Meta:
        model = CourseSection
        fields = [
            "id",
            "parent",
            "title",
            "order",
            "content",
            "summary",
            "objectives",
            "estimated_minutes",
        ]
        read_only_fields = ["id"]


class CourseSectionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for editing section / lesson content by teachers or users."""

    class Meta:
        model = CourseSection
        fields = [
            "parent",
            "title",
            "order",
            "content",
            "summary",
            "objectives",
            "estimated_minutes",
        ]


class CourseGenerateRequestSerializer(serializers.Serializer):
    """Options for AI-powered course generation from an analyzed document."""

    document_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text="UUID optionnel du document analysé à transformer en cours",
    )
    provider = serializers.CharField(
        required=False,
        default=None,
        allow_null=True,
        help_text="Fournisseur LLM (mock, openai, anthropic, gemini, local)",
    )
    model = serializers.CharField(
        required=False,
        default=None,
        allow_null=True,
        help_text="Modèle spécifique LLM",
    )
    focus = serializers.CharField(
        required=False,
        default=None,
        allow_null=True,
        allow_blank=True,
        help_text="Directive pédagogique spécifique",
    )
    top_k = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=30,
        help_text="Nombre de segments RAG à analyser",
    )
    language = serializers.ChoiceField(
        choices=["fr", "ar", "en"],
        required=False,
        default="fr",
        allow_null=True,
        help_text="Langue du cours à générer (fr, ar, en)",
    )
    level = serializers.ChoiceField(
        choices=CourseLevel.choices,
        required=False,
        default=None,
        allow_null=True,
        help_text="Niveau d'apprentissage ciblé",
    )
    preserve_existing = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Préserver les sections/chapitres déjà existants au lieu de les remplacer",
    )
    async_mode = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Exécuter la génération en arrière-plan via Celery",
    )
