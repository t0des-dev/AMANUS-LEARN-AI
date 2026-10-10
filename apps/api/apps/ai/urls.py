from django.urls import path

from .views import RAGQueryView, RAGSearchView, TaskStatusView

app_name = "rag"

urlpatterns = [
    path("search/", RAGSearchView.as_view(), name="rag-search"),
    path("query/", RAGQueryView.as_view(), name="rag-query"),
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),
]
