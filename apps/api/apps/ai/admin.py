from django.contrib import admin

from .models import AIGeneration


@admin.register(AIGeneration)
class AIGenerationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "type",
        "status",
        "provider",
        "model",
        "prompt_version",
        "input_tokens",
        "output_tokens",
        "organization",
        "created_at",
    )
    list_filter = ("type", "status", "provider", "created_at")
    search_fields = ("document__title", "organization__name", "user__email")
    readonly_fields = ("id", "created_at")
