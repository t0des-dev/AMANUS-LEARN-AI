from django.urls import path

from apps.audio.views import SectionAudioView

from .views import SectionDetailView

app_name = "sections"

urlpatterns = [
    path("<uuid:id>", SectionDetailView.as_view(), name="section-detail-no-slash"),
    path("<uuid:id>/", SectionDetailView.as_view(), name="section-detail"),
    path("<uuid:id>/audio", SectionAudioView.as_view(), name="section-audio-no-slash"),
    path("<uuid:id>/audio/", SectionAudioView.as_view(), name="section-audio"),
]
