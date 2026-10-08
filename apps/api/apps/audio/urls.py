from django.urls import path

from .views import AudioDetailView, VoicesListView

app_name = "audio"

urlpatterns = [
    path("voices", VoicesListView.as_view(), name="voices-list-no-slash"),
    path("voices/", VoicesListView.as_view(), name="voices-list"),
    path("<uuid:id>", AudioDetailView.as_view(), name="audio-detail-no-slash"),
    path("<uuid:id>/", AudioDetailView.as_view(), name="audio-detail"),
]
