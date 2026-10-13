from django.urls import path

from .views import (
    AudioDetailView,
    PodcastEpisodeDetailView,
    PodcastEpisodeListCreateView,
    VoicesListView,
)

app_name = "audio"

urlpatterns = [
    path("voices", VoicesListView.as_view(), name="voices-list-no-slash"),
    path("voices/", VoicesListView.as_view(), name="voices-list"),
    path("podcasts/", PodcastEpisodeListCreateView.as_view(), name="podcast-list-create"),
    path("podcasts/<uuid:id>/", PodcastEpisodeDetailView.as_view(), name="podcast-detail"),
    path("<uuid:id>", AudioDetailView.as_view(), name="audio-detail-no-slash"),
    path("<uuid:id>/", AudioDetailView.as_view(), name="audio-detail"),
]
