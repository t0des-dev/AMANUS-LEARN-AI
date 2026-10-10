import logging
from uuid import UUID

from django.db import transaction
from django.db.models import Max
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.models import Course
from apps.courses.permissions import CanManageCourse
from apps.slides.models import (
    Presentation,
    PresentationSlide,
    PresentationStatus,
    PresentationTheme,
)
from apps.slides.permissions import CanManagePresentation, IsPresentationOrganizationMember
from apps.slides.serializers import (
    PresentationCreateSerializer,
    PresentationDetailSerializer,
    PresentationListSerializer,
    PresentationSlideCreateUpdateSerializer,
    PresentationSlideSerializer,
    PresentationUpdateSerializer,
    SlideOrderItemSerializer,
)
from apps.slides.services.pptx_exporter import PPTXExporter
from apps.slides.services.slide_generator import SlideGenerator
from apps.slides.tasks import export_presentation_task

logger = logging.getLogger(__name__)


class CoursePresentationsView(APIView):
    """POST /api/v1/courses/{id}/presentations/ - Generate a presentation from a Course.
    GET  /api/v1/courses/{id}/presentations/ - List all presentations for a Course.
    """

    permission_classes = [IsAuthenticated]

    def _get_course(self, course_id: UUID) -> Course:
        course = get_object_or_404(Course, id=course_id)
        if not course.organization.is_member(self.request.user):
            raise PermissionDenied("Vous n'avez pas accès aux présentations de ce cours.")
        return course

    def get(self, request, id: UUID):
        course = self._get_course(id)
        presentations = Presentation.objects.filter(course=course).prefetch_related("slides")
        serializer = PresentationListSerializer(presentations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, id: UUID):
        course = self._get_course(id)
        # Verify management permission on the course
        perm = CanManageCourse()
        if not perm.has_object_permission(request, self, course):
            raise PermissionDenied(
                "Vous n'avez pas les droits nécessaires pour générer des présentations."
            )

        input_serializer = PresentationCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data

        title = data.get("title") or course.title
        theme = data.get("theme", PresentationTheme.MODERN_DARK)
        language = data.get("language")
        level = data.get("level")
        focus = data.get("focus")

        generator = SlideGenerator()
        presentation = generator.generate_presentation(
            course=course,
            title=title,
            theme=theme,
            language=language,
            level=level,
            focus=focus,
        )

        output_serializer = PresentationDetailSerializer(presentation)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class PresentationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/v1/presentations/{id}/ — Get presentation details with slides.
    PATCH  /api/v1/presentations/{id}/ — Update presentation (title, theme, slide reordering).
    DELETE /api/v1/presentations/{id}/ — Delete presentation.
    """

    queryset = (
        Presentation.objects.all()
        .select_related("course", "course__organization")
        .prefetch_related("slides")
    )
    permission_classes = [IsAuthenticated, IsPresentationOrganizationMember]
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return PresentationUpdateSerializer
        return PresentationDetailSerializer

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated(), IsPresentationOrganizationMember()]
        return [IsAuthenticated(), CanManagePresentation()]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        instance.refresh_from_db()
        out = PresentationDetailSerializer(instance)
        return Response(out.data)


class PresentationExportView(APIView):
    """POST /api/v1/presentations/{id}/export/ — Export presentation as PPTX.

    Supports synchronous export (default) or async celery task (via ?async=true or {"async": true}).
    """

    permission_classes = [IsAuthenticated, CanManagePresentation]

    def post(self, request, id: UUID):
        presentation = get_object_or_404(
            Presentation.objects.select_related("course", "course__organization").prefetch_related(
                "slides"
            ),
            id=id,
        )
        self.check_object_permissions(request, presentation)

        # Validate that presentation has slides to export
        from apps.slides.services.validator import (
            InvalidPresentationPayloadError,
            PresentationValidator,
        )

        if presentation.status == PresentationStatus.EXPORTING:
            return Response(
                {
                    "detail": "Une exportation PPTX est déjà en cours pour cette présentation.",
                    "code": "export_already_in_progress",
                },
                status=status.HTTP_409_CONFLICT,
            )

        try:
            PresentationValidator.validate_deck_for_export(presentation)
        except InvalidPresentationPayloadError as exc:
            return Response(
                {"detail": str(exc), "code": "empty_presentation"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        is_async = request.query_params.get("async", "").lower() in ("true", "1") or bool(
            request.data.get("async")
        )

        if is_async:
            presentation.status = PresentationStatus.EXPORTING
            presentation.save(update_fields=["status", "updated_at"])
            task = export_presentation_task.delay(str(presentation.id))
            return Response(
                {
                    "status": PresentationStatus.EXPORTING,
                    "task_id": str(task.id),
                    "message": "Exportation PPTX en cours d'exécution en arrière-plan.",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        # Synchronous execution
        exporter = PPTXExporter()
        try:
            storage_key = exporter.export_and_save(presentation)
        except InvalidPresentationPayloadError as exc:
            return Response(
                {"detail": str(exc), "code": "invalid_deck"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        presentation.refresh_from_db()

        serializer = PresentationDetailSerializer(presentation)
        return Response(
            {
                "status": presentation.status,
                "storage_key": storage_key,
                "export_url": presentation.get_export_url(),
                "presentation": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class PresentationSlideListCreateView(APIView):
    """POST /api/v1/presentations/{id}/slides/ — Add a new slide to a presentation."""

    permission_classes = [IsAuthenticated, CanManagePresentation]

    def post(self, request, id: UUID):
        presentation = get_object_or_404(Presentation, id=id)
        self.check_object_permissions(request, presentation)

        serializer = PresentationSlideCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        slide_num = data.get("slide_number")
        if not slide_num:
            max_num = presentation.slides.aggregate(Max("slide_number"))["slide_number__max"] or 0
            slide_num = max_num + 1

        slide = PresentationSlide.objects.create(
            presentation=presentation,
            slide_number=slide_num,
            title=data.get("title", f"Slide {slide_num}"),
            content=data.get("content", ""),
            speaker_notes=data.get("speaker_notes", ""),
            image_prompt=data.get("image_prompt", ""),
            image_url=data.get("image_url", ""),
        )

        return Response(PresentationSlideSerializer(slide).data, status=status.HTTP_201_CREATED)


class PresentationSlideDetailView(APIView):
    """PATCH  /api/v1/presentations/{id}/slides/{slide_id}/ — Update slide content/title.
    DELETE /api/v1/presentations/{id}/slides/{slide_id}/ — Remove slide from presentation.
    """

    permission_classes = [IsAuthenticated, CanManagePresentation]

    def _get_slide_and_presentation(
        self, pres_id: UUID, slide_id: UUID
    ) -> tuple[Presentation, PresentationSlide]:
        presentation = get_object_or_404(Presentation, id=pres_id)
        self.check_object_permissions(self.request, presentation)
        slide = get_object_or_404(PresentationSlide, id=slide_id, presentation=presentation)
        return presentation, slide

    def patch(self, request, id: UUID, slide_id: UUID):
        presentation, slide = self._get_slide_and_presentation(id, slide_id)
        serializer = PresentationSlideCreateUpdateSerializer(slide, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PresentationSlideSerializer(slide).data, status=status.HTTP_200_OK)

    def delete(self, request, id: UUID, slide_id: UUID):
        presentation, slide = self._get_slide_and_presentation(id, slide_id)
        deleted_order = slide.slide_number
        slide.delete()

        # Renumber subsequent slides to prevent gaps
        with transaction.atomic():
            subsequent_slides = presentation.slides.filter(slide_number__gt=deleted_order).order_by(
                "slide_number"
            )
            for item in subsequent_slides:
                item.slide_number -= 1
                item.save(update_fields=["slide_number"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class PresentationReorderView(APIView):
    """POST /api/v1/presentations/{id}/reorder/ — Bulk reorder slides."""

    permission_classes = [IsAuthenticated, CanManagePresentation]

    def post(self, request, id: UUID):
        presentation = get_object_or_404(Presentation, id=id)
        self.check_object_permissions(request, presentation)

        orders = request.data if isinstance(request.data, list) else request.data.get("slides", [])
        serializer = SlideOrderItemSerializer(data=orders, many=True)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            for item in serializer.validated_data:
                presentation.slides.filter(id=item["id"]).update(slide_number=item["slide_number"])

        presentation.refresh_from_db()
        return Response(PresentationDetailSerializer(presentation).data, status=status.HTTP_200_OK)
