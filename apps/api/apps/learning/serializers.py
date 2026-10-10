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
