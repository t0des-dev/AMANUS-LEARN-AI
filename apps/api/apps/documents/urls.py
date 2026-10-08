from django.urls import path

from apps.ai.views import (
    DocumentGenerateCourseView,
    DocumentGenerateKeyPointsView,
    DocumentGenerateObjectivesView,
    DocumentGenerateRevisionSheetView,
    DocumentGenerateSummaryView,
)
from apps.ingestion.views import (
    DocumentPagesListView,
    DocumentProcessingStatusView,
)

from .views import (
    DocumentDetailView,
    DocumentListCreateView,
    DocumentProcessView,
    DocumentStatusView,
)

app_name = "documents"

urlpatterns = [
    path("", DocumentListCreateView.as_view(), name="document-list-create"),
    path("<uuid:id>/", DocumentDetailView.as_view(), name="document-detail"),
    path("<uuid:id>/process/", DocumentProcessView.as_view(), name="document-process"),
    path("<uuid:id>/status/", DocumentStatusView.as_view(), name="document-status"),
    path(
        "<uuid:id>/processing-status/",
        DocumentProcessingStatusView.as_view(),
        name="document-processing-status",
    ),
    path("<uuid:id>/pages/", DocumentPagesListView.as_view(), name="document-pages"),
    # SPRINT 06 — AI Generation Endpoints
    path(
        "<uuid:id>/generate/summary/",
        DocumentGenerateSummaryView.as_view(),
        name="document-generate-summary",
    ),
    path(
        "<uuid:id>/generate/course/",
        DocumentGenerateCourseView.as_view(),
        name="document-generate-course",
    ),
    path(
        "<uuid:id>/generate/objectives/",
        DocumentGenerateObjectivesView.as_view(),
        name="document-generate-objectives",
    ),
    path(
        "<uuid:id>/generate/key-points/",
        DocumentGenerateKeyPointsView.as_view(),
        name="document-generate-key-points",
    ),
    path(
        "<uuid:id>/generate/revision-sheet/",
        DocumentGenerateRevisionSheetView.as_view(),
        name="document-generate-revision-sheet",
    ),
]
