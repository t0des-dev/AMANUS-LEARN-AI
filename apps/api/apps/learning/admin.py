from django.contrib import admin

from .models import LearningPath, LearningProgress, StudySession


@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "status", "progress", "started_at", "completed_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("user__email", "course__title")
    ordering = ("-updated_at",)


@admin.register(LearningProgress)
class LearningProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "section", "completion_percent", "last_position", "score", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "course__title", "section__title")
    ordering = ("-updated_at",)


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "started_at", "ended_at", "duration")
    list_filter = ("started_at",)
    search_fields = ("user__email", "course__title")
    ordering = ("-started_at",)
