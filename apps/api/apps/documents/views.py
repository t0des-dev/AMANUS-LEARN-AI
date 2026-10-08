import logging

from django.db.models import Q
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.models import Organization

from .models import Document, DocumentStatus
from .permissions import CanManageDocument, IsDocumentOrganizationMember
from .serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentStatusSerializer,
    DocumentUpdateSerializer,
    DocumentUploadSerializer,
)
from .services.storage import get_storage_service
from .tasks import process_document_pipeline

logger = logging.getLogger(__name__)


class DocumentListCreateView(generics.ListCreateAPIView):
    """GET  /api/v1/documents - List documents isolated by organization

    POST /api/v1/documents - Upload document (PDF, DOCX, PPTX, TXT)
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return DocumentUploadSerializer
        return DocumentListSerializer

    def get_queryset(self):
        user = self.request.user
        # Strict isolation: only documents from organizations where user is a member
        queryset = Document.objects.filter(organization__members__user=user).select_related(
            "organization", "owner"
        )

        # Optional filter by organization_id
        org_id = self.request.query_params.get("organization_id")
        if org_id:
            # Verify user has membership in requested organization
            if not Organization.objects.filter(id=org_id, members__user=user).exists():
                raise PermissionDenied("Vous n'avez pas accès aux documents de cette organisation.")
            queryset = queryset.filter(organization_id=org_id)

        # Optional filter by status
        doc_status = self.request.query_params.get("status")
        if doc_status and doc_status in DocumentStatus.values:
            queryset = queryset.filter(status=doc_status)

        # Optional text search
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(file_name__icontains=search)
                | Q(description__icontains=search)
            )

        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        document = serializer.save()
        read_serializer = DocumentDetailSerializer(document, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET    /api/v1/documents/{id} - Retrieve document details

    PATCH  /api/v1/documents/{id} - Update document metadata
    DELETE /api/v1/documents/{id} - Delete document and purge file from storage
    """

    lookup_field = "id"
    lookup_url_kwarg = "id"
    permission_classes = [IsAuthenticated, CanManageDocument]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return DocumentUpdateSerializer
        return DocumentDetailSerializer

    def get_queryset(self):
        # Strict isolation: tenant membership required
        return Document.objects.filter(
            organization__members__user=self.request.user
        ).select_related("organization", "owner")

    def perform_destroy(self, instance: Document):
        storage_key = instance.storage_key
        # Purge file from storage
        storage = get_storage_service()
        try:
            storage.delete_file(storage_key)
        except Exception as e:
            logger.warning(f"Error purging file from storage on delete ({storage_key}): {e}")
        instance.delete()


class DocumentProcessView(APIView):
    """POST /api/v1/documents/{id}/process - Trigger pipeline staging for document."""

    permission_classes = [IsAuthenticated, CanManageDocument]

    def post(self, request, id):
        try:
            # Strict tenant isolation
            document = Document.objects.get(
                id=id,
                organization__members__user=request.user,
            )
        except Document.DoesNotExist:
            return Response(
                {"detail": "Document introuvable ou non autorisé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        self.check_object_permissions(request, document)

        # Trigger Celery background task (or run synchronously if eager/in-test)
        try:
            task_result = process_document_pipeline.delay(str(document.id))
            task_id = getattr(task_result, "id", None)
        except Exception as e:
            logger.warning(f"Celery dispatch failed ({e}), executing pipeline synchronously.")
            process_document_pipeline(str(document.id))
            task_id = "sync"

        document.refresh_from_db()

        return Response(
            {
                "id": str(document.id),
                "status": document.status,
                "task_id": task_id,
                "message": "Pipeline de traitement initialisé avec succès.",
            },
            status=status.HTTP_200_OK,
        )


class DocumentStatusView(APIView):
    """GET /api/v1/documents/{id}/status - Check processing lifecycle status."""

    permission_classes = [IsAuthenticated, IsDocumentOrganizationMember]

    def get(self, request, id):
        try:
            # Strict tenant isolation
            document = Document.objects.get(
                id=id,
                organization__members__user=request.user,
            )
        except Document.DoesNotExist:
            return Response(
                {"detail": "Document introuvable ou non autorisé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        self.check_object_permissions(request, document)
        serializer = DocumentStatusSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)
