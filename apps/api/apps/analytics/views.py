import logging
from uuid import UUID

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.permissions import CanViewTeacherAnalytics
from apps.analytics.services.analytics_service import AnalyticsService
from apps.courses.models import Course
from apps.quizzes.models import Quiz

logger = logging.getLogger(__name__)


class StudentAnalyticsView(APIView):
    """GET /api/v1/analytics/student/ — Student personal learning analytics."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        service = AnalyticsService()
        data = service.get_student_analytics(request.user)
        return Response(data, status=status.HTTP_200_OK)


class CourseAnalyticsView(APIView):
    """GET /api/v1/analytics/courses/{id}/ — Instructor course analytics (enrollment, progress, problematic chapters)."""

    permission_classes = [IsAuthenticated, CanViewTeacherAnalytics]

    def get(self, request, id: UUID):
        course = get_object_or_404(
            Course.objects.select_related("organization", "created_by").prefetch_related(
                "sections"
            ),
            id=id,
        )
        self.check_object_permissions(request, course)

        service = AnalyticsService()
        data = service.get_course_analytics(course)
        return Response(data, status=status.HTTP_200_OK)


class CourseStudentsAnalyticsView(APIView):
    """GET /api/v1/analytics/courses/{id}/students/ — Per-student performance and study duration in a course."""

    permission_classes = [IsAuthenticated, CanViewTeacherAnalytics]

    def get(self, request, id: UUID):
        course = get_object_or_404(
            Course.objects.select_related("organization", "created_by"),
            id=id,
        )
        self.check_object_permissions(request, course)

        service = AnalyticsService()
        students_data = service.get_course_students_performance(course)
        return Response(students_data, status=status.HTTP_200_OK)


class QuizAnalyticsView(APIView):
    """GET /api/v1/analytics/quizzes/{id}/ — Quiz analytics with difficult questions analysis."""

    permission_classes = [IsAuthenticated, CanViewTeacherAnalytics]

    def get(self, request, id: UUID):
        quiz = get_object_or_404(
            Quiz.objects.select_related("organization", "course", "created_by").prefetch_related(
                "questions", "attempts"
            ),
            id=id,
        )
        self.check_object_permissions(request, quiz)

        service = AnalyticsService()
        data = service.get_quiz_analytics(quiz)
        return Response(data, status=status.HTTP_200_OK)
