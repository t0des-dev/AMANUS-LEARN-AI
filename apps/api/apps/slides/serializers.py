from rest_framework import serializers

from apps.slides.models import Presentation, PresentationSlide, PresentationTheme


class PresentationSlideSerializer(serializers.ModelSerializer):
    """Serializer for individual presentation slides."""

    class Meta:
        model = PresentationSlide
        fields = [
            "id",
            "presentation",
            "slide_number",
            "title",
            "content",
            "speaker_notes",
            "image_prompt",
            "image_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "presentation", "created_at", "updated_at"]


class PresentationSlideCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating or updating a single slide."""

    slide_number = serializers.IntegerField(required=False)

    class Meta:
        model = PresentationSlide
        fields = [
            "id",
            "slide_number",
            "title",
            "content",
            "speaker_notes",
            "image_prompt",
            "image_url",
        ]
        read_only_fields = ["id"]


class SlideOrderItemSerializer(serializers.Serializer):
    """Item specification for bulk reordering slides."""

    id = serializers.UUIDField()
    slide_number = serializers.IntegerField(min_value=1)


class PresentationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for presentations with nested slides and export link."""

    slides = PresentationSlideSerializer(many=True, read_only=True)
    export_url = serializers.SerializerMethodField()
    course_title = serializers.CharField(source="course.title", read_only=True)
    slides_count = serializers.SerializerMethodField()

    class Meta:
        model = Presentation
        fields = [
            "id",
            "course",
            "course_title",
            "title",
            "theme",
            "status",
            "storage_key",
            "export_url",
            "slides_count",
            "slides",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "course",
            "course_title",
            "status",
            "storage_key",
            "export_url",
            "slides_count",
            "slides",
            "created_at",
            "updated_at",
        ]

    def get_export_url(self, obj: Presentation) -> str | None:
        return obj.get_export_url()

    def get_slides_count(self, obj: Presentation) -> int:
        return obj.slides.count()


class PresentationListSerializer(serializers.ModelSerializer):
    """Concise serializer for listing presentations."""

    export_url = serializers.SerializerMethodField()
    course_title = serializers.CharField(source="course.title", read_only=True)
    slides_count = serializers.SerializerMethodField()

    class Meta:
        model = Presentation
        fields = [
            "id",
            "course",
            "course_title",
            "title",
            "theme",
            "status",
            "storage_key",
            "export_url",
            "slides_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_export_url(self, obj: Presentation) -> str | None:
        return obj.get_export_url()

    def get_slides_count(self, obj: Presentation) -> int:
        return obj.slides.count()


class PresentationCreateSerializer(serializers.Serializer):
    """Input payload for generating a presentation from a Course."""

    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    theme = serializers.ChoiceField(
        choices=PresentationTheme.choices,
        default=PresentationTheme.MODERN_DARK,
        required=False,
    )


class PresentationUpdateSerializer(serializers.ModelSerializer):
    """Payload for patching presentation metadata and optional slide orders."""

    slides_order = serializers.ListField(
        child=SlideOrderItemSerializer(),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Presentation
        fields = ["title", "theme", "slides_order"]

    def update(self, instance: Presentation, validated_data: dict) -> Presentation:
        slides_order = validated_data.pop("slides_order", None)
        instance = super().update(instance, validated_data)

        if slides_order:
            for item in slides_order:
                instance.slides.filter(id=item["id"]).update(slide_number=item["slide_number"])

        return instance
