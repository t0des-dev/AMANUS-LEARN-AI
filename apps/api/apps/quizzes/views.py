import logging
import uuid

from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course
from apps.documents.models import Document
from apps.organizations.models import Organization, RoleChoices

from .models import Quiz, QuizAttempt
from .permissions import CanManageQuiz, IsQuizOrganizationMember
from .serializers import (
    QuizAttemptSerializer,
    QuizCreateSerializer,
    QuizDetailSerializer,
    QuizGenerateRequestSerializer,
    QuizListSerializer,
    QuizSubmitPayloadSerializer,
)
from .services import (
    InvalidQuizQuestionError,
    QuizAttemptService,
    QuizGeneratorService,
)

logger = logging.getLogger(__name__)


class QuizListCreateView(generics.ListCreateAPIView):
    """GET  /api/v1/quizzes/ — List quizzes accessible to user.

    POST /api/v1/quizzes/ — Create a new quiz.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return QuizCreateSerializer
        return QuizListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Quiz.objects.filter(organization__members__user=user)
            .select_related("organization", "course", "document")
            .prefetch_related("questions")
        )

        org_id = self.request.query_params.get("organization_id")
        if org_id:
            if not Organization.objects.filter(id=org_id, members__user=user).exists():
                raise PermissionDenied("Vous n'avez pas accès aux quiz de cette organisation.")
            queryset = queryset.filter(organization_id=org_id)

        course_id = self.request.query_params.get("course_id")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        quiz_type = self.request.query_params.get("type")
        if quiz_type:
            queryset = queryset.filter(type=quiz_type)

        difficulty = self.request.query_params.get("difficulty")
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        organization = serializer.validated_data["organization"]

        # Only TEACHER, ADMIN, OWNER can create quizzes
        role = organization.get_user_role(user)
        if role not in (RoleChoices.OWNER, RoleChoices.ADMIN, RoleChoices.TEACHER):
            raise PermissionDenied(
                "Seuls les enseignants et administrateurs peuvent créer des QCM."
            )

        serializer.save(created_by=user)


class CourseQuizzesView(APIView):
    """GET  /api/v1/courses/{id}/quizzes — List quizzes belonging to a specific course.

    POST /api/v1/courses/{id}/quizzes — Create a quiz attached to this course.
    """

    permission_classes = [IsAuthenticated]

    def get_course(self, course_id: uuid.UUID) -> Course:
        course = get_object_or_404(Course, id=course_id)
        if not course.organization.is_member(self.request.user):
            raise PermissionDenied(
                "Vous n'êtes pas membre de l'organisation propriétaire de ce cours."
            )
        return course

    def get(self, request, id: uuid.UUID):
        course = self.get_course(id)
        quizzes = Quiz.objects.filter(course=course).order_by("-created_at")
        serializer = QuizListSerializer(quizzes, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, id: uuid.UUID):
        course = self.get_course(id)
        role = course.organization.get_user_role(request.user)
        if role not in (RoleChoices.OWNER, RoleChoices.ADMIN, RoleChoices.TEACHER):
            raise PermissionDenied("Seuls les enseignants peuvent créer des quiz pour ce cours.")

        data = request.data.copy()
        data["organization"] = str(course.organization_id)
        data["course"] = str(course.id)
        if not data.get("document") and course.document:
            data["document"] = str(course.document_id)

        serializer = QuizCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save(created_by=request.user)

        # Optional auto-generation if requested
        if request.data.get("generate_ai", False):
            doc = quiz.document or course.document
            if doc:
                gen_service = QuizGeneratorService()
                try:
                    gen_service.generate_questions_for_quiz(
                        quiz=quiz,
                        document=doc,
                        count=int(request.data.get("questions_count", 5)),
                        provider_name=request.data.get("provider"),
                        model=request.data.get("model"),
                        focus=request.data.get("focus"),
                    )
                except Exception as exc:
                    logger.warning("Auto-generation failed during quiz creation: %s", exc)

        out_serializer = QuizDetailSerializer(quiz, context={"request": request})
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/v1/quizzes/{id}/ — Detail of quiz with questions.

    PATCH  /api/v1/quizzes/{id}/ — Update quiz metadata.
    DELETE /api/v1/quizzes/{id}/ — Delete quiz.
    """

    permission_classes = [IsAuthenticated, CanManageQuiz]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        return (
            Quiz.objects.filter(organization__members__user=user)
            .select_related("organization", "course", "document")
            .prefetch_related("questions__answers")
        )

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return QuizCreateSerializer
        return QuizDetailSerializer


class QuizGenerateView(APIView):
    """POST /api/v1/quizzes/{id}/generate/

    Generates multiple choice questions using AI and RAG extraction from document.
    Enforces strict validation of all questions before database insertion.
    """

    permission_classes = [IsAuthenticated, CanManageQuiz]

    def post(self, request, id: uuid.UUID):
        quiz = get_object_or_404(
            Quiz.objects.select_related("organization", "document", "course"),
            id=id,
        )
        self.check_object_permissions(request, quiz)

        serializer = QuizGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        doc_id = data.get("document_id")
        if doc_id:
            document = get_object_or_404(Document, id=doc_id, organization=quiz.organization)
        elif quiz.document:
            document = quiz.document
        elif quiz.course and quiz.course.document:
            document = quiz.course.document
        else:
            return Response(
                {
                    "detail": "Aucun document source n'est lié à ce quiz. Veuillez fournir un document_id.",
                    "code": "missing_document",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        gen_service = QuizGeneratorService()
        try:
            created_questions = gen_service.generate_questions_for_quiz(
                quiz=quiz,
                document=document,
                provider_name=data.get("provider"),
                model=data.get("model"),
                count=data.get("count", 5),
                focus=data.get("focus"),
                top_k=data.get("top_k", 8),
            )

            out_serializer = QuizDetailSerializer(quiz, context={"request": request})
            return Response(
                {
                    "quiz": out_serializer.data,
                    "generated_count": len(created_questions),
                },
                status=status.HTTP_200_OK,
            )
        except InvalidQuizQuestionError as val_err:
            return Response(
                {"detail": str(val_err), "code": "invalid_questions"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except Exception as exc:
            logger.exception("Quiz generation error: %s", exc)
            return Response(
                {"detail": f"Erreur lors de la génération IA : {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class QuizStartAttemptView(APIView):
    """POST /api/v1/quizzes/{id}/start — Initializes a quiz attempt session."""

    permission_classes = [IsAuthenticated, IsQuizOrganizationMember]

    def post(self, request, id: uuid.UUID):
        quiz = get_object_or_404(Quiz.objects.select_related("organization"), id=id)
        self.check_object_permissions(request, quiz)

        if quiz.questions.count() == 0:
            return Response(
                {
                    "detail": "Ce QCM ne contient aucune question pour le moment.",
                    "code": "empty_quiz",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = QuizAttemptService()
        attempt = service.start_attempt(quiz, request.user)
        serializer = QuizAttemptSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuizSubmitAttemptView(APIView):
    """POST /api/v1/quizzes/{id}/submit — Submits answers, calculates score, and evaluates results."""

    permission_classes = [IsAuthenticated, IsQuizOrganizationMember]

    def post(self, request, id: uuid.UUID):
        quiz = get_object_or_404(Quiz.objects.select_related("organization"), id=id)
        self.check_object_permissions(request, quiz)

        serializer = QuizSubmitPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers_dict = serializer.validated_data["answers"]

        attempt_id = request.data.get("attempt_id")
        service = QuizAttemptService()

        if attempt_id:
            attempt = get_object_or_404(QuizAttempt, id=attempt_id, quiz=quiz, user=request.user)
        else:
            # Look for active unfinished attempt or start a fresh one
            attempt = (
                QuizAttempt.objects.filter(quiz=quiz, user=request.user, completed_at__isnull=True)
                .order_by("-started_at")
                .first()
            )
            if not attempt:
                attempt = service.start_attempt(quiz, request.user)

        evaluation = service.submit_attempt(attempt=attempt, submitted_answers=answers_dict)
        return Response(evaluation, status=status.HTTP_200_OK)


class QuizResultsHistoryView(APIView):
    """GET /api/v1/quizzes/{id}/results — Retrieves user attempts and best performance for this quiz."""

    permission_classes = [IsAuthenticated, IsQuizOrganizationMember]

    def get(self, request, id: uuid.UUID):
        quiz = get_object_or_404(Quiz.objects.select_related("organization"), id=id)
        self.check_object_permissions(request, quiz)

        attempts = QuizAttempt.objects.filter(
            quiz=quiz, user=request.user, completed_at__isnull=False
        ).order_by("-started_at")

        serializer = QuizAttemptSerializer(attempts, many=True)
        best_score = max([a.score for a in attempts]) if attempts.exists() else 0.0
        has_passed = any(a.passed for a in attempts)

        return Response(
            {
                "quiz_id": str(quiz.id),
                "quiz_title": quiz.title,
                "passing_score": quiz.passing_score_percentage,
                "best_score": best_score,
                "has_passed": has_passed,
                "total_attempts": len(attempts),
                "attempts": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
