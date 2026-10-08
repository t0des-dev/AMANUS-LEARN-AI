from django.urls import path

from .views import DocumentPagesListView, DocumentProcessingStatusView

app_name = "ingestion"

urlpatterns = [
    path(
        "documents/<uuid:id>/processing-status/",
        DocumentProcessingStatusView.as_view(),
        name="document-processing-status",
    ),
    path("documents/<uuid:id>/pages/", DocumentPagesListView.as_view(), name="document-pages"),
]
