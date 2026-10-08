from django.urls import path

from .views import (
    CourseLearningProgressView,
    LearningCoursesListView,
    LearningDashboardView,
    SectionCompleteView,
    StudySessionFinishView,
    StudySessionStartView,
)

app_name = "learning"

urlpatterns = [
    path("dashboard/", LearningDashboardView.as_view(), name="learning-dashboard"),
    path("courses/", LearningCoursesListView.as_view(), name="learning-courses"),
    path("courses/<uuid:id>/progress/", CourseLearningProgressView.as_view(), name="course-learning-progress"),
    path("sections/<uuid:id>/complete/", SectionCompleteView.as_view(), name="section-complete"),
    path("sessions/start/", StudySessionStartView.as_view(), name="study-session-start"),
    path("sessions/<uuid:id>/finish/", StudySessionFinishView.as_view(), name="study-session-finish"),
]
