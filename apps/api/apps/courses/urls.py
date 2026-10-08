from django.urls import path

from apps.quizzes.views import CourseQuizzesView
from apps.slides.views import CoursePresentationsView

from .views import (
    CourseDetailView,
    CourseGenerateView,
    CourseListCreateView,
    CourseSectionsListCreateView,
)

app_name = "courses"

urlpatterns = [
    path("", CourseListCreateView.as_view(), name="course-list-create"),
    path("<uuid:id>/", CourseDetailView.as_view(), name="course-detail"),
    path(
        "<uuid:id>/sections/",
        CourseSectionsListCreateView.as_view(),
        name="course-sections-list-create",
    ),
    path(
        "<uuid:id>/generate/",
        CourseGenerateView.as_view(),
        name="course-generate",
    ),
    path(
        "<uuid:id>/quizzes/",
        CourseQuizzesView.as_view(),
        name="course-quizzes",
    ),
    path(
        "<uuid:id>/presentations/",
        CoursePresentationsView.as_view(),
        name="course-presentations",
    ),
]
