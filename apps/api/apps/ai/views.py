import logging
import time
import uuid

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai.serializers import (
    AIGenerationSerializer,
    GenerateRequestSerializer,
    RAGSearchRequestSerializer,
)
from apps.ai.services import (
    AIService,
    InsufficientContextError,
    Retriever,
)
from apps.documents.models import Document
from apps.organizations.models import OrganizationMember

logger = logging.getLogger(__name__)


class RAGBaseView(APIView):
    """Base class enforcing strict multi-tenant validation for RAG endpoints."""

    permission_classes = [IsAuthenticated]

    def validate_tenant_access(
        self, request, org_id: str, doc_id: str | None = None
    ) -> tuple[bool, Response | None]:
        """Validates that request.user belongs to organization and document is in tenant."""
        is_member = OrganizationMember.objects.filter(
            organization_id=org_id,
            user=request.user,
        ).exists()

        if not is_member:
            return False, Response(
                {"detail": "Accès refusé : vous n'êtes pas membre de cette organisation."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if doc_id:
            doc_exists = Document.objects.filter(
                id=doc_id,
                organization_id=org_id,
            ).exists()
            if not doc_exists:
                return False, Response(
                    {"detail": "Document introuvable dans cette organisation."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return True, None


class RAGSearchView(RAGBaseView):
    """POST /api/v1/rag/search/

    Semantic vector search with organization multi-tenant filtering,
    re-ranking, and structured provenance metadata.
    """

    def post(self, request):
        serializer = RAGSearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        org_id = str(data["organization_id"])
        doc_id = str(data["document_id"]) if data.get("document_id") else None
        query = data["query"]
        top_k = data.get("top_k", 5)
        search_mode = data.get("search_mode", "hybrid")
        min_score = data.get("min_score", 0.0)
        use_cache = data.get("use_cache", True)

        is_valid, error_response = self.validate_tenant_access(request, org_id, doc_id)
        if not is_valid:
            return error_response

        retriever = Retriever()
        start_time = time.perf_counter()
        results = retriever.search_sources(
            query=query,
            organization_id=org_id,
            document_id=doc_id,
            top_k=top_k,
            search_mode=search_mode,
            min_score=min_score,
            use_cache=use_cache,
        )
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        response_payload = {
            "query": query,
            "organization_id": org_id,
            "document_id": doc_id,
            "count": len(results),
            "search_mode": search_mode,
            "latency_ms": latency_ms,
            "results": results,
        }
        return Response(response_payload, status=status.HTTP_200_OK)


class RAGQueryView(RAGBaseView):
    """POST /api/v1/rag/query/

    Executes complete RAG retrieval pipeline: hybrid/semantic/lexical search, re-ranking,
    grounded context generation, and structured citations.
    """

    def post(self, request):
        serializer = RAGSearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        org_id = str(data["organization_id"])
        doc_id = str(data["document_id"]) if data.get("document_id") else None
        query = data["query"]
        top_k = data.get("top_k", 5)
        search_mode = data.get("search_mode", "hybrid")
        min_score = data.get("min_score", 0.0)
        use_cache = data.get("use_cache", True)

        is_valid, error_response = self.validate_tenant_access(request, org_id, doc_id)
        if not is_valid:
            return error_response

        retriever = Retriever()
        query_result = retriever.query(
            query=query,
            organization_id=org_id,
            document_id=doc_id,
            top_k=top_k,
            search_mode=search_mode,
            min_score=min_score,
            use_cache=use_cache,
        )

        return Response(query_result, status=status.HTTP_200_OK)


# =========================================================================
# SPRINT 06 — AI Generation Views
# =========================================================================


class DocumentGenerateBaseView(APIView):
    """Base class for document AI generation endpoints.

    Enforces multi-tenant authorization and dispatches requests strictly
    through AIService facade (never directly to AI providers).
    """

    permission_classes = [IsAuthenticated]

    def get_document(
        self, request, doc_id: uuid.UUID | str
    ) -> tuple[Document | None, Response | None]:
        doc = get_object_or_404(Document, id=doc_id)

        # Multi-tenant check: user must belong to the document's organization
        if not doc.organization.is_member(request.user):
            return None, Response(
                {
                    "detail": "Accès refusé : vous n'êtes pas membre de l'organisation propriétaire de ce document."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        return doc, None

    def execute_generation(self, request, doc_id, generation_method_name: str):
        doc, err_response = self.get_document(request, doc_id)
        if err_response:
            return err_response

        serializer = GenerateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from apps.billing.models import UsageMetric
        from apps.billing.services.quota_service import QuotaService

        reservation = QuotaService.reserve_quota(
            organization=doc.organization,
            metric=UsageMetric.AI_GENERATIONS,
            amount=1,
            user=request.user,
            idempotency_key=f"doc_gen_{doc.id}_{generation_method_name}_{uuid.uuid4().hex[:8]}",
            estimated_cost_usd=0.010,
        )

        ai_service = AIService()
        generation_method = getattr(ai_service, generation_method_name)

        gen_kwargs = {
            "document": doc,
            "user": request.user,
            "provider_name": data.get("provider"),
            "model": data.get("model"),
            "focus": data.get("focus"),
            "top_k": data.get("top_k", 5),
            "language": data.get("language"),
            "level": data.get("level"),
        }
        if generation_method_name == "generate_summary" and data.get("summary_level"):
            gen_kwargs["summary_level"] = data.get("summary_level")

        try:
            record = generation_method(**gen_kwargs)
            QuotaService.commit_quota(reservation.id, actual_amount=1, actual_cost_usd=0.010)

            out_serializer = AIGenerationSerializer(record)
            return Response(out_serializer.data, status=status.HTTP_201_CREATED)

        except InsufficientContextError as exc:
            QuotaService.release_quota(reservation.id, reason=str(exc))
            return Response(
                {
                    "detail": str(exc),
                    "code": "insufficient_context",
                    "document_id": str(doc.id),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            QuotaService.release_quota(reservation.id, reason=str(exc))
            logger.exception("AI generation failed for doc %s: %s", doc_id, exc)
            return Response(
                {"detail": f"Erreur lors de la génération IA : {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DocumentGenerateSummaryView(DocumentGenerateBaseView):
    """POST /api/v1/documents/{id}/generate/summary

    Generates a structured, grounded summary from document RAG chunks.
    """

    def post(self, request, id):
        return self.execute_generation(request, id, "generate_summary")


class DocumentGenerateCourseView(DocumentGenerateBaseView):
    """POST /api/v1/documents/{id}/generate/course

    Generates a pedagogical course/lesson from document RAG chunks.
    """

    def post(self, request, id):
        return self.execute_generation(request, id, "generate_course")


class DocumentGenerateObjectivesView(DocumentGenerateBaseView):
    """POST /api/v1/documents/{id}/generate/objectives

    Generates structured learning objectives from document RAG chunks.
    """

    def post(self, request, id):
        return self.execute_generation(request, id, "generate_objectives")


class DocumentGenerateKeyPointsView(DocumentGenerateBaseView):
    """POST /api/v1/documents/{id}/generate/key-points

    Extracts essential key points and core concepts from document RAG chunks.
    """

    def post(self, request, id):
        return self.execute_generation(request, id, "generate_key_points")


class DocumentGenerateRevisionSheetView(DocumentGenerateBaseView):
    """POST /api/v1/documents/{id}/generate/revision-sheet

    Generates an exam revision sheet from document RAG chunks.
    """

    def post(self, request, id):
        return self.execute_generation(request, id, "generate_revision_sheet")


class TaskStatusView(APIView):
    """GET /api/v1/ai/tasks/{task_id}/ (and /api/v1/tasks/{task_id}/)

    Returns the unified lifecycle status, progress, duration, and result of any background generation task.
    Enforces strict multi-tenant authorization.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, task_id: str):
        from apps.ai.services.orchestration import TaskAccessDeniedError, TaskTracker

        try:
            status_data = TaskTracker.get_task_status(task_id, user=request.user)
            return Response(status_data, status=status.HTTP_200_OK)
        except TaskAccessDeniedError as err:
            return Response(
                {"detail": str(err), "code": "task_access_denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as exc:
            logger.exception("Error checking task status for %s: %s", task_id, exc)
            return Response(
                {"detail": f"Erreur lors de la récupération du statut : {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
