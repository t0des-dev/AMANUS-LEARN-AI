import logging
import uuid

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document
from apps.organizations.models import Organization, RoleChoices

from .models import Course, CourseSection
from .permissions import CanManageCourse, IsCourseOrganizationMember
from .serializers import (
    CourseCreateSerializer,
    CourseDetailSerializer,
    CourseGenerateRequestSerializer,
    CourseListSerializer,
    CourseSectionCreateSerializer,
    CourseSectionSerializer,
    CourseSectionTreeSerializer,
    CourseSectionUpdateSerializer,
    CourseUpdateSerializer,
)
from .services import CourseBuilderService

logger = logging.getLogger(__name__)


class CourseListCreateView(generics.ListCreateAPIView):
    """GET  /api/v1/courses/ — List courses accessible to the authenticated user.

    POST /api/v1/courses/ — Create a new course in an organization.
    """

    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CourseCreateSerializer
        return CourseListSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = (
            Course.objects.filter(organization__members__user=user)
            .select_related("organization", "created_by", "document")
            .prefetch_related("sections")
        )

        org_id = self.request.query_params.get("organization_id")
        if org_id:
            if not Organization.objects.filter(id=org_id, members__user=user).exists():
                raise PermissionDenied("Vous n'avez pas accès aux cours de cette organisation.")
            queryset = queryset.filter(organization_id=org_id)

        course_status = self.request.query_params.get("status")
        if course_status:
            queryset = queryset.filter(status=course_status)

        course_level = self.request.query_params.get("level")
        if course_level:
            queryset = queryset.filter(level=course_level)

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        organization = serializer.validated_data["organization"]

        # Only TEACHER, ADMIN, OWNER can create courses
        role = organization.get_user_role(user)
        if role not in (RoleChoices.OWNER, RoleChoices.ADMIN, RoleChoices.TEACHER):
            raise PermissionDenied(
                "Seuls les enseignants et administrateurs peuvent créer des cours."
            )

        serializer.save(created_by=user)


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/v1/courses/{id}/ — Course detail with full hierarchical outline.

    PATCH  /api/v1/courses/{id}/ — Update course metadata (Teacher/Admin/Owner).
    DELETE /api/v1/courses/{id}/ — Delete course (Teacher/Admin/Owner).
    """

    permission_classes = [IsAuthenticated, CanManageCourse]
    lookup_field = "id"

    def get_queryset(self):
        user = self.request.user
        return (
            Course.objects.filter(organization__members__user=user)
            .select_related("organization", "created_by", "document")
            .prefetch_related("sections__children")
        )

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return CourseUpdateSerializer
        return CourseDetailSerializer


class CourseSectionsListCreateView(generics.ListCreateAPIView):
    """GET  /api/v1/courses/{id}/sections/ — List hierarchical sections/chapters of a course.

    POST /api/v1/courses/{id}/sections/ — Add a new section, chapter or lesson.
    """

    permission_classes = [IsAuthenticated, CanManageCourse]

    def get_course(self) -> Course:
        course_id = self.kwargs["id"]
        course = get_object_or_404(Course, id=course_id)
        # Check permissions
        self.check_object_permissions(self.request, course)
        return course

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CourseSectionCreateSerializer
        return CourseSectionTreeSerializer

    def get_queryset(self):
        course = self.get_course()
        # Return root sections (Chapters) for tree structure
        return course.sections.filter(parent__isnull=True).prefetch_related("children__children")

    def perform_create(self, serializer):
        course = self.get_course()
        # Ensure parent section (if given) belongs to the same course
        parent = serializer.validated_data.get("parent")
        if parent and parent.course_id != course.id:
            raise ValidationError({"parent": "La section parente doit appartenir au même cours."})

        serializer.save(course=course)


class SectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/v1/sections/{id}/ — Section / lesson details.

    PATCH  /api/v1/sections/{id}/ — Edit section or lesson content (Teacher editable AI content).
    DELETE /api/v1/sections/{id}/ — Delete section or lesson.
    """

    permission_classes = [IsAuthenticated, CanManageCourse]
    lookup_field = "id"
    queryset = CourseSection.objects.select_related("course__organization")

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return CourseSectionUpdateSerializer
        return CourseSectionSerializer


class CourseGenerateView(APIView):
    """POST /api/v1/courses/{id}/generate/

    Transforms an analyzed document into a structured pedagogical course:
    Course -> Chapter -> Section -> Lesson.
    All generated content remains fully editable by teachers.
    """

    permission_classes = [IsAuthenticated, CanManageCourse]

    def post(self, request, id: uuid.UUID):
        course = get_object_or_404(Course.objects.select_related("organization", "document"), id=id)
        self.check_object_permissions(request, course)

        serializer = CourseGenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        doc_id = data.get("document_id")
        if doc_id:
            document = get_object_or_404(Document, id=doc_id, organization=course.organization)
        elif course.document:
            document = course.document
        else:
            return Response(
                {
                    "detail": "Aucun document source n'est associé à ce cours. Veuillez spécifier un document_id.",
                    "code": "missing_document",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Ensure document is ingested and has text chunks for RAG
        from apps.documents.models import DocumentStatus
        if document.chunks.count() == 0:
            try:
                from apps.ingestion.tasks import create_chunks, extract_document
                logger.info("Auto-triggering ingestion for document %s before course generation", document.id)
                extract_document(str(document.id))
                create_chunks(str(document.id))
                document.refresh_from_db()
                document.status = DocumentStatus.READY
                document.save(update_fields=["status", "updated_at"])
            except Exception as ing_err:
                logger.warning("Auto-ingestion attempt for doc %s failed: %s", document.id, ing_err)

        from apps.ai.services.orchestration import (
            ConcurrentGenerationConflictError,
            GenerationLock,
            IdempotencyManager,
        )

        idempotency_key = request.headers.get("Idempotency-Key") or request.query_params.get(
            "idempotency_key"
        )
        if idempotency_key:
            cached_res = IdempotencyManager.get_existing_result(idempotency_key)
            if cached_res:
                return Response(cached_res, status=status.HTTP_200_OK)

        from apps.billing.models import UsageMetric
        from apps.billing.services.quota_service import QuotaService

        # 1. Atomic Quota Reservation
        res_key = idempotency_key or f"course_gen_{course.id}_{uuid.uuid4().hex[:8]}"
        reservation = QuotaService.reserve_quota(
            organization=course.organization,
            metric=UsageMetric.AI_GENERATIONS,
            amount=1,
            user=request.user,
            idempotency_key=res_key,
            estimated_cost_usd=0.015,
        )

        # 2. Concurrency guard
        try:
            GenerationLock.acquire(
                "course", str(course.id), owner_id=str(request.user.id if request.user else "anon")
            )
        except ConcurrentGenerationConflictError as lock_err:
            QuotaService.release_quota(reservation.id, reason="conflict")
            return Response(
                {
                    "detail": str(lock_err),
                    "code": "generation_in_progress",
                    "course_id": str(course.id),
                },
                status=status.HTTP_409_CONFLICT,
            )

        builder = CourseBuilderService()
        if data.get("async_mode"):
            from apps.courses.tasks import generate_course_task

            task = generate_course_task.delay(
                course_id=str(course.id),
                document_id=str(document.id),
                user_id=request.user.id if request.user else None,
                provider=data.get("provider"),
                model=data.get("model"),
                focus=data.get("focus"),
                top_k=data.get("top_k", 10),
                language=data.get("language"),
                level=data.get("level"),
                preserve_existing=data.get("preserve_existing", False),
            )
            reservation.task_id = str(task.id)
            reservation.save(update_fields=["task_id"])

            response_payload = {
                "status": "PENDING",
                "task_id": task.id,
                "course_id": str(course.id),
                "reservation_id": str(reservation.id),
                "message": "Génération du cours initiée en arrière-plan.",
            }
            if idempotency_key:
                IdempotencyManager.record_result(idempotency_key, response_payload)
            return Response(
                response_payload,
                status=status.HTTP_202_ACCEPTED,
            )

        try:
            updated_course = builder.generate_course_from_document(
                course=course,
                document=document,
                user=request.user,
                provider_name=data.get("provider"),
                model=data.get("model"),
                focus=data.get("focus"),
                top_k=data.get("top_k", 10),
                language=data.get("language"),
                level=data.get("level"),
                preserve_existing=data.get("preserve_existing", False),
            )
            # Confirm quota consumption
            QuotaService.commit_quota(reservation.id, actual_amount=1, actual_cost_usd=0.015)

            out_serializer = CourseDetailSerializer(updated_course)
            if idempotency_key:
                IdempotencyManager.record_result(idempotency_key, out_serializer.data)
            return Response(out_serializer.data, status=status.HTTP_200_OK)

        except Exception as exc:
            QuotaService.release_quota(reservation.id, reason=str(exc))
            logger.exception("Course generation failed for course %s: %s", id, exc)
            return Response(
                {
                    "detail": f"Échec de la génération du cours : {exc}",
                    "code": "generation_failed",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        finally:
            GenerationLock.release("course", str(course.id))


class CourseExportDocxView(APIView):
    """GET /api/v1/courses/{id}/export/docx/ — Export course as formatted Microsoft Word (.docx) document."""

    permission_classes = [IsAuthenticated, IsCourseOrganizationMember]

    def get(self, request, id: uuid.UUID):
        from apps.courses.services.docx_exporter import CourseDocxExporter

        course = get_object_or_404(
            Course.objects.filter(organization__members__user=request.user)
            .select_related("organization")
            .prefetch_related("sections__children"),
            id=id,
        )
        exporter = CourseDocxExporter(course)
        buffer = exporter.generate()

        safe_title = "".join(c for c in course.title if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        filename = f"{safe_title or 'cours'}.docx"

        response = HttpResponse(
            buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class CourseExportMarkdownView(APIView):
    """GET /api/v1/courses/{id}/export/markdown/ — Export course as clean Markdown (.md) document."""

    permission_classes = [IsAuthenticated, IsCourseOrganizationMember]

    def get(self, request, id: uuid.UUID):
        course = get_object_or_404(
            Course.objects.filter(organization__members__user=request.user)
            .select_related("organization")
            .prefetch_related("sections__children"),
            id=id,
        )
        lines = [f"# {course.title}\n"]
        if course.description:
            lines.append(f"> {course.description}\n")
        lines.append(f"**Niveau :** {course.get_level_display()} | **Langue :** {course.language.upper()}\n\n---\n")

        chapters = (
            course.sections.filter(parent__isnull=True)
            .order_by("order", "created_at")
            .prefetch_related("children")
        )
        for ch in chapters:
            lines.append(f"## {ch.title}\n")
            if ch.summary:
                lines.append(f"*{ch.summary}*\n")
            for sec in ch.children.all().order_by("order", "created_at"):
                lines.append(f"### {sec.title}\n")
                if sec.objectives and isinstance(sec.objectives, list):
                    lines.append("**Objectifs :**")
                    for obj in sec.objectives:
                        lines.append(f"- {obj}")
                    lines.append("")
                if sec.content:
                    lines.append(f"{sec.content}\n")

        content = "\n".join(lines)
        safe_title = "".join(c for c in course.title if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
        filename = f"{safe_title or 'cours'}.md"

        response = HttpResponse(content, content_type="text/markdown; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

