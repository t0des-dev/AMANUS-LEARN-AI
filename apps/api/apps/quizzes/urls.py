from django.urls import path

from .views import (
    QuizDetailView,
    QuizGenerateView,
    QuizListCreateView,
    QuizResultsHistoryView,
    QuizStartAttemptView,
    QuizSubmitAttemptView,
    UserQuizHistoryView,
)

app_name = "quizzes"

urlpatterns = [
    path("", QuizListCreateView.as_view(), name="quiz-list-create"),
    path("history/", UserQuizHistoryView.as_view(), name="quiz-user-history"),
    path("<uuid:id>/", QuizDetailView.as_view(), name="quiz-detail"),
    path(
        "<uuid:id>/generate/",
        QuizGenerateView.as_view(),
        name="quiz-generate",
    ),
    path(
        "<uuid:id>/start/",
        QuizStartAttemptView.as_view(),
        name="quiz-start",
    ),
    path(
        "<uuid:id>/submit/",
        QuizSubmitAttemptView.as_view(),
        name="quiz-submit",
    ),
    path(
        "<uuid:id>/results/",
        QuizResultsHistoryView.as_view(),
        name="quiz-results",
    ),
]
