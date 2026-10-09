import logging
from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course, CourseSection
from apps.learning.models import LearningPath, StudySession
from apps.learning.serializers import (
    LearningPathSerializer,
    LearningProgressSerializer,
    SectionCompleteRequestSerializer,
    StudySessionSerializer,
    StudySessionStartSerializer,
)
from apps.learning.services.learning_engine import LearningEngine

logger = logging.getLogger(__name__)


class LearningDashboardView(APIView):
    """GET /api/v1/learning/dashboard/ — Student dashboard with real computed metrics."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        engine = LearningEngine()
        dashboard_data = engine.get_student_dashboard(request.user)
        return Response(dashboard_data, status=status.HTTP_200_OK)


class LearningCoursesListView(generics.ListAPIView):
    """GET /api/v1/learning/courses/ — List all courses tracked in the user's learning paths."""

    permission_classes = [IsAuthenticated]
    serializer_class = LearningPathSerializer

    def get_queryset(self):
        return (
            LearningPath.objects.filter(user=self.request.user)
            .select_related("course", "course__organization")
            .order_by("-updated_at")
        )


class CourseLearningProgressView(APIView):
    """GET /api/v1/learning/courses/{id}/progress/ — Granular progress breakdown for a course."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id: UUID):
        course = get_object_or_404(Course, id=id)
        if not course.organization.is_member(request.user):
            raise PermissionDenied("Vous n'êtes pas membre de l'organisation dispensant ce cours.")

        engine = LearningEngine()
        progress_data = engine.get_course_progress(request.user, course)
        return Response(progress_data, status=status.HTTP_200_OK)


class SectionCompleteView(APIView):
    """POST /api/v1/learning/sections/{id}/complete/ — Mark section progress / completion."""

    permission_classes = [IsAuthenticated]

    def post(self, request, id: UUID):
        section = get_object_or_404(CourseSection.objects.select_related("course", "course__organization"), id=id)
        if not section.course.organization.is_member(request.user):
            raise PermissionDenied("Vous n'avez pas accès à ce cours.")

        serializer = SectionCompleteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        engine = LearningEngine()
        progress, path = engine.record_section_progress(
            user=request.user,
            section=section,
            completion_percent=data.get("completion_percent", 100.0),
            last_position=data.get("last_position", 0),
            score=data.get("score"),
        )

        return Response(
            {
                "progress": LearningProgressSerializer(progress).data,
                "course_progress": path.progress,
                "course_status": path.status,
            },
            status=status.HTTP_200_OK,
        )


class StudySessionStartView(APIView):
    """POST /api/v1/learning/sessions/start/ — Start tracking an active study session."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StudySessionStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course_id = serializer.validated_data["course_id"]

        course = get_object_or_404(Course.objects.select_related("organization"), id=course_id)
        if not course.organization.is_member(request.user):
            raise PermissionDenied("Vous n'avez pas accès à ce cours.")

        engine = LearningEngine()
        session = engine.start_study_session(user=request.user, course=course)
        return Response(StudySessionSerializer(session).data, status=status.HTTP_201_CREATED)


class StudySessionFinishView(APIView):
    """POST /api/v1/learning/sessions/{id}/finish/ — Conclude a study session and record duration."""

    permission_classes = [IsAuthenticated]

    def post(self, request, id: UUID):
        session = get_object_or_404(StudySession, id=id, user=request.user)
        engine = LearningEngine()
        finished_session = engine.finish_study_session(user=request.user, session_id=session.id)
        return Response(StudySessionSerializer(finished_session).data, status=status.HTTP_200_OK)
