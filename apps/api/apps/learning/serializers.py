from rest_framework import serializers

from apps.courses.models import Course
from apps.learning.models import LearningPath, LearningProgress, StudySession


class CourseMinimalSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source="organization.name", read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "level", "status", "organization_name"]


class LearningPathSerializer(serializers.ModelSerializer):
    course = CourseMinimalSerializer(read_only=True)

    class Meta:
        model = LearningPath
        fields = [
            "id",
            "course",
            "status",
            "progress",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]


class LearningProgressSerializer(serializers.ModelSerializer):
    section_title = serializers.CharField(source="section.title", read_only=True)
    section_order = serializers.IntegerField(source="section.order", read_only=True)

    class Meta:
        model = LearningProgress
        fields = [
            "id",
            "course",
            "section",
            "section_title",
            "section_order",
            "completion_percent",
            "is_completed",
            "completed_at",
            "last_viewed_at",
            "last_position",
            "score",
            "created_at",
            "updated_at",
        ]


class SectionCompleteRequestSerializer(serializers.Serializer):
    completion_percent = serializers.FloatField(
        default=100.0,
        min_value=0.0,
        max_value=100.0,
        required=False,
    )
    is_completed = serializers.BooleanField(
        required=False,
        default=None,
        allow_null=True,
    )
    last_position = serializers.IntegerField(default=0, min_value=0, required=False)
    score = serializers.FloatField(
        min_value=0.0,
        max_value=100.0,
        required=False,
        allow_null=True,
    )


class StudySessionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = StudySession
        fields = [
            "id",
            "course",
            "course_title",
            "started_at",
            "ended_at",
            "duration",
            "created_at",
        ]


class StudySessionStartSerializer(serializers.Serializer):
    course_id = serializers.UUIDField(required=True)


class FlashcardSerializer(serializers.ModelSerializer):
    review_info = serializers.SerializerMethodField()

    class Meta:
        from apps.learning.models import Flashcard

        model = Flashcard
        fields = [
            "id",
            "deck",
            "front",
            "back",
            "hint",
            "source_citation",
            "order",
            "review_info",
            "created_at",
        ]

    def get_review_info(self, obj):
        request = self.context.get("request")
        if not request or not request.user or not request.user.is_authenticated:
            return None
        review = obj.reviews.filter(user=request.user).first()
        if not review:
            return {
                "repetitions": 0,
                "interval_days": 0,
                "ease_factor": 2.5,
                "is_due": True,
                "next_review_at": None,
            }
        from django.utils import timezone

        return {
            "repetitions": review.repetitions,
            "interval_days": review.interval_days,
            "ease_factor": review.ease_factor,
            "last_quality": review.last_quality,
            "is_due": review.next_review_at <= timezone.now(),
            "next_review_at": review.next_review_at,
        }


class FlashcardDeckSerializer(serializers.ModelSerializer):
    cards_count = serializers.IntegerField(source="cards.count", read_only=True)
    cards = FlashcardSerializer(many=True, read_only=True)

    class Meta:
        from apps.learning.models import FlashcardDeck

        model = FlashcardDeck
        fields = [
            "id",
            "organization",
            "course",
            "document",
            "title",
            "description",
            "cards_count",
            "cards",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class FlashcardDeckCreateSerializer(serializers.Serializer):
    organization_id = serializers.UUIDField(required=True)
    course_id = serializers.UUIDField(required=False, allow_null=True)
    document_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    cards = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        default=list,
    )


class FlashcardReviewSubmitSerializer(serializers.Serializer):
    quality = serializers.IntegerField(min_value=0, max_value=5, required=True)

