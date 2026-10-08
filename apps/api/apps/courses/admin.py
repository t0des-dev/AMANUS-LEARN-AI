from django.contrib import admin

from .models import Course, CourseSection


class CourseSectionInline(admin.TabularInline):
    model = CourseSection
    extra = 1
    fields = ("title", "parent", "order", "estimated_minutes")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "organization",
        "level",
        "status",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "level", "created_at")
    search_fields = ("title", "description", "organization__name")
    inlines = [CourseSectionInline]


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "course",
        "parent",
        "order",
        "estimated_minutes",
        "created_at",
    )
    list_filter = ("course", "created_at")
    search_fields = ("title", "content", "summary")
