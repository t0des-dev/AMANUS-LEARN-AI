from django.contrib import admin

from .models import ChatMessage, ChatSession


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "organization", "document", "course", "updated_at")
    list_filter = ("organization", "created_at")
    search_fields = ("title", "user__email", "user__username")


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "command", "tokens_used", "created_at")
    list_filter = ("role", "command", "created_at")
    search_fields = ("content", "session__title")
