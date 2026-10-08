from django.contrib import admin

from .models import Presentation, PresentationSlide


class PresentationSlideInline(admin.TabularInline):
    model = PresentationSlide
    extra = 1
    fields = ("slide_number", "title", "content", "speaker_notes")


@admin.register(Presentation)
class PresentationAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "theme", "status", "created_at")
    list_filter = ("theme", "status", "created_at")
    search_fields = ("title", "course__title")
    inlines = [PresentationSlideInline]


@admin.register(PresentationSlide)
class PresentationSlideAdmin(admin.ModelAdmin):
    list_display = ("presentation", "slide_number", "title", "created_at")
    list_filter = ("presentation__theme", "created_at")
    search_fields = ("title", "content", "speaker_notes")
