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
        section = get_object_or_404(
            CourseSection.objects.select_related("course", "course__organization"), id=id
        )
        if not section.course.organization.is_member(request.user):
            raise PermissionDenied("Vous n'avez pas accès à ce cours.")

        serializer = SectionCompleteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        raw_pct = data.get("completion_percent")
        is_completed = data.get("is_completed")

        if is_completed is True:
            comp_pct = 100.0
        elif raw_pct is not None:
            comp_pct = raw_pct
        elif is_completed is False:
            comp_pct = 0.0
        else:
            # Default when called with empty payload
            comp_pct = 100.0
            is_completed = True

        engine = LearningEngine()
        progress, path = engine.record_section_progress(
            user=request.user,
            section=section,
            completion_percent=comp_pct,
            last_position=data.get("last_position", 0),
            score=data.get("score"),
            is_completed=is_completed,
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


class FlashcardDeckListCreateView(APIView):
    """GET  /api/v1/learning/flashcard-decks/ - List decks isolated by organization.
    POST /api/v1/learning/flashcard-decks/ - Create or save a new deck of flashcards.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.learning.models import FlashcardDeck
        from apps.learning.serializers import FlashcardDeckSerializer

        queryset = FlashcardDeck.objects.filter(
            organization__members__user=request.user
        ).select_related("organization", "course", "document").prefetch_related("cards")

        course_id = request.query_params.get("course_id")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        document_id = request.query_params.get("document_id")
        if document_id:
            queryset = queryset.filter(document_id=document_id)

        serializer = FlashcardDeckSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        from apps.learning.models import Flashcard, FlashcardDeck
        from apps.learning.serializers import FlashcardDeckCreateSerializer, FlashcardDeckSerializer
        from apps.organizations.models import Organization

        create_serializer = FlashcardDeckCreateSerializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        data = create_serializer.validated_data

        org = get_object_or_404(Organization, id=data["organization_id"])
        if not org.is_member(request.user):
            raise PermissionDenied("Vous n'êtes pas membre de cette organisation.")

        deck = FlashcardDeck.objects.create(
            organization=org,
            course_id=data.get("course_id"),
            document_id=data.get("document_id"),
            created_by=request.user,
            title=data["title"],
            description=data.get("description", ""),
        )

        cards_data = data.get("cards", [])
        for idx, c in enumerate(cards_data):
            Flashcard.objects.create(
                deck=deck,
                front=c.get("front", ""),
                back=c.get("back", ""),
                hint=c.get("hint", ""),
                source_citation=c.get("source_citation", ""),
                order=idx + 1,
            )

        deck.refresh_from_db()
        return Response(
            FlashcardDeckSerializer(deck, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class FlashcardDeckDetailView(APIView):
    """GET /api/v1/learning/flashcard-decks/{id}/ - Retrieve a deck with all its flashcards."""

    permission_classes = [IsAuthenticated]

    def get(self, request, id: UUID):
        from apps.learning.models import FlashcardDeck
        from apps.learning.serializers import FlashcardDeckSerializer

        deck = get_object_or_404(
            FlashcardDeck.objects.filter(organization__members__user=request.user)
            .select_related("organization", "course", "document")
            .prefetch_related("cards"),
            id=id,
        )
        return Response(FlashcardDeckSerializer(deck, context={"request": request}).data, status=status.HTTP_200_OK)


class FlashcardReviewSubmitView(APIView):
    """POST /api/v1/learning/flashcards/{card_id}/review/ - Submit study evaluation (0-5) and compute next SM-2 interval."""

    permission_classes = [IsAuthenticated]

    def post(self, request, card_id: UUID):
        from apps.learning.models import Flashcard, FlashcardReview
        from apps.learning.serializers import FlashcardReviewSubmitSerializer

        card = get_object_or_404(
            Flashcard.objects.filter(deck__organization__members__user=request.user),
            id=card_id,
        )
        serializer = FlashcardReviewSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quality = serializer.validated_data["quality"]
        review, _ = FlashcardReview.objects.get_or_create(user=request.user, card=card)
        review.record_review(quality)

        return Response(
            {
                "card_id": str(card.id),
                "quality": quality,
                "repetitions": review.repetitions,
                "interval_days": review.interval_days,
                "ease_factor": review.ease_factor,
                "next_review_at": review.next_review_at,
            },
            status=status.HTTP_200_OK,
        )

