from django.contrib import admin

from .models import AudioContent


@admin.register(AudioContent)
class AudioContentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "section",
        "course",
        "voice_provider",
        "voice_id",
        "duration",
        "status",
        "created_at",
    )
    list_filter = ("status", "voice_provider", "language")
    search_fields = ("section__title", "course__title", "script")
