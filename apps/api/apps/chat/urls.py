from django.urls import path

from .views import (
    ChatMessageCreateView,
    ChatSessionDetailView,
    ChatSessionListCreateView,
    PedagogicalCommandsListView,
)

app_name = "chat"

urlpatterns = [
    # Pedagogical Commands
    path("commands", PedagogicalCommandsListView.as_view(), name="commands-no-slash"),
    path("commands/", PedagogicalCommandsListView.as_view(), name="commands"),
    # Sessions
    path("sessions", ChatSessionListCreateView.as_view(), name="session-list-create-no-slash"),
    path("sessions/", ChatSessionListCreateView.as_view(), name="session-list-create"),
    path("sessions/<uuid:id>", ChatSessionDetailView.as_view(), name="session-detail-no-slash"),
    path("sessions/<uuid:id>/", ChatSessionDetailView.as_view(), name="session-detail"),
    path("sessions/<uuid:id>/messages", ChatMessageCreateView.as_view(), name="session-messages-no-slash"),
    path("sessions/<uuid:id>/messages/", ChatMessageCreateView.as_view(), name="session-messages"),
]
