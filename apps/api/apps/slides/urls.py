from django.urls import path

from .views import (
    PresentationDetailView,
    PresentationExportView,
    PresentationReorderView,
    PresentationSlideDetailView,
    PresentationSlideListCreateView,
)

app_name = "slides"

urlpatterns = [
    path("<uuid:id>/", PresentationDetailView.as_view(), name="presentation-detail"),
    path("<uuid:id>/export/", PresentationExportView.as_view(), name="presentation-export"),
    path(
        "<uuid:id>/slides/",
        PresentationSlideListCreateView.as_view(),
        name="presentation-slide-list-create",
    ),
    path(
        "<uuid:id>/slides/<uuid:slide_id>/",
        PresentationSlideDetailView.as_view(),
        name="presentation-slide-detail",
    ),
    path("<uuid:id>/reorder/", PresentationReorderView.as_view(), name="presentation-reorder"),
]
