import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.documents.models import Document
from apps.documents.permissions import IsDocumentOrganizationMember
from apps.ingestion.serializers import (
    DocumentPageSerializer,
    DocumentProcessingStatusSerializer,
)

logger = logging.getLogger(__name__)


class DocumentProcessingStatusView(APIView):
    """GET /api/v1/documents/{id}/processing-status/

    Returns the fine-grained lifecycle progression of the document
    (Uploading, Extracting, OCR, Structuring, Chunking, Completed, Failed).
    """

    permission_classes = [IsAuthenticated, IsDocumentOrganizationMember]

    def get(self, request, id):
        try:
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
        serializer = DocumentProcessingStatusSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentPagesListView(APIView):
    """GET /api/v1/documents/{id}/pages/

    Returns extracted pages and their hierarchical structure for the document.
    """

    permission_classes = [IsAuthenticated, IsDocumentOrganizationMember]

    def get(self, request, id):
        try:
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
        pages = document.pages.all().order_by("page_number")
        serializer = DocumentPageSerializer(pages, many=True)
        return Response(
            {
                "count": pages.count(),
                "document_id": str(document.id),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )
