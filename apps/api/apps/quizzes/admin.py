from django.contrib import admin

from .models import Quiz, QuizAnswer, QuizAttempt, QuizQuestion


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 4
    fields = ("text", "is_correct", "order")


class QuizQuestionInline(admin.StackedInline):
    model = QuizQuestion
    extra = 1
    fields = ("text", "difficulty", "source", "explanation", "order")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "organization",
        "course",
        "type",
        "difficulty",
        "time_limit_minutes",
        "passing_score_percentage",
        "status",
        "created_at",
    )
    list_filter = ("type", "difficulty", "status", "created_at")
    search_fields = ("title", "description", "organization__name")
    inlines = [QuizQuestionInline]


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "quiz", "text", "difficulty", "source", "order")
    list_filter = ("difficulty", "quiz")
    search_fields = ("text", "explanation", "source")
    inlines = [QuizAnswerInline]


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "text", "is_correct", "order")
    list_filter = ("is_correct",)
    search_fields = ("text",)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "quiz",
        "user",
        "score",
        "correct_answers_count",
        "total_questions",
        "passed",
        "started_at",
        "completed_at",
    )
    list_filter = ("passed", "started_at")
    search_fields = ("user__email", "quiz__title")
