from django.urls import path

from .views import (
    CourseAnalyticsView,
    CourseStudentsAnalyticsView,
    QuizAnalyticsView,
    StudentAnalyticsView,
)

app_name = "analytics"

urlpatterns = [
    path("student/", StudentAnalyticsView.as_view(), name="student-analytics"),
    path("courses/<uuid:id>/", CourseAnalyticsView.as_view(), name="course-analytics"),
    path(
        "courses/<uuid:id>/students/",
        CourseStudentsAnalyticsView.as_view(),
        name="course-students-analytics",
    ),
    path("quizzes/<uuid:id>/", QuizAnalyticsView.as_view(), name="quiz-analytics"),
]
