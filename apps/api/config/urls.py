"""URL configuration for Amanus Learn AI API."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.ai.views import TaskStatusView
from apps.billing.views import SystemHealthView

from .views import HealthCheckView

# API v1 routes
v1_patterns = [
    path("health", HealthCheckView.as_view(), name="health-check"),
    path("health/", HealthCheckView.as_view(), name="health-check-slash"),
    path("system/health", SystemHealthView.as_view(), name="v1-system-health"),
    path("system/health/", SystemHealthView.as_view(), name="v1-system-health-slash"),
    path("auth/", include("apps.accounts.urls")),
    path("organizations/", include("apps.organizations.urls")),
    path("documents/", include("apps.documents.urls")),
    path("rag/", include("apps.ai.urls")),
    path("ai/", include("apps.ai.urls")),
    path("courses/", include("apps.courses.urls")),
    path("sections/", include("apps.courses.section_urls")),
    path("quizzes/", include("apps.quizzes.urls")),
    path("chat/", include("apps.chat.urls")),
    path("audio/", include("apps.audio.urls")),
    path("presentations/", include("apps.slides.urls")),
    path("slides/presentations/", include("apps.slides.urls")),
    path("learning/", include("apps.learning.urls")),
    path("analytics/", include("apps.analytics.urls")),
    path("billing/", include("apps.billing.urls")),
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="v1-task-status"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    # Top-level direct routes for SaaS specifications
    path("billing/", include("apps.billing.urls")),
    path("system/health", SystemHealthView.as_view(), name="root-system-health"),
    path("system/health/", SystemHealthView.as_view(), name="root-system-health-slash"),
    # API Version 1
    path("api/v1/", include((v1_patterns, "v1"))),
    # OpenAPI 3 Schema & Docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
