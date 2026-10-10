from rest_framework import serializers

from apps.organizations.models import RoleChoices

from .models import (
    Quiz,
    QuizAnswer,
    QuizAttempt,
    QuizQuestion,
)


class QuizAnswerSerializer(serializers.ModelSerializer):
    """Full answer serialization including is_correct flag (for teachers and results review)."""

    class Meta:
        model = QuizAnswer
        fields = ["id", "text", "is_correct", "order"]


class QuizAnswerStudentSerializer(serializers.ModelSerializer):
    """Public answer option for taking a quiz. Never leaks is_correct to students."""

    class Meta:
        model = QuizAnswer
        fields = ["id", "text", "order"]


class QuizQuestionSerializer(serializers.ModelSerializer):
    """Question serializer with answers and pedagogical explanations.

    Protects both correct answers and explanations from premature leakage to students
    before they submit their attempt.
    """

    answers = serializers.SerializerMethodField()
    explanation = serializers.SerializerMethodField()

    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "text",
            "explanation",
            "difficulty",
            "source",
            "order",
            "answers",
            "created_at",
        ]

    def _should_reveal(self, obj: QuizQuestion) -> bool:
        request = self.context.get("request")
        is_teacher = False
        if request and request.user and request.user.is_authenticated:
            org = obj.quiz.organization
            role = org.get_user_role(request.user)
            if role in (RoleChoices.OWNER, RoleChoices.ADMIN, RoleChoices.TEACHER):
                is_teacher = True

        return bool(self.context.get("reveal_correct", False) or is_teacher)

    def get_answers(self, obj: QuizQuestion):
        if self._should_reveal(obj):
            return QuizAnswerSerializer(obj.answers.all(), many=True).data
        return QuizAnswerStudentSerializer(obj.answers.all(), many=True).data

    def get_explanation(self, obj: QuizQuestion):
        if self._should_reveal(obj):
            return obj.explanation
        return ""


class QuizListSerializer(serializers.ModelSerializer):
    """Listing serialization with question metrics."""

    questions_count = serializers.SerializerMethodField()
    organization_name = serializers.CharField(source="organization.name", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True, default=None)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "organization",
            "organization_name",
            "course",
            "course_title",
            "document",
            "title",
            "description",
            "type",
            "difficulty",
            "time_limit_minutes",
            "passing_score_percentage",
            "status",
            "questions_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "questions_count",
            "created_at",
            "updated_at",
        ]

    def get_questions_count(self, obj: Quiz) -> int:
        return obj.questions.count()


class QuizDetailSerializer(QuizListSerializer):
    """Detailed quiz with its ordered questions and options."""

    questions = serializers.SerializerMethodField()

    class Meta(QuizListSerializer.Meta):
        fields = QuizListSerializer.Meta.fields + ["questions"]

    def get_questions(self, obj: Quiz):
        context = self.context
        return QuizQuestionSerializer(
            obj.questions.all().order_by("order", "created_at"),
            many=True,
            context=context,
        ).data


class QuizCreateSerializer(serializers.ModelSerializer):
    """Serializer for manual or AI-assisted Quiz creation."""

    class Meta:
        model = Quiz
        fields = [
            "id",
            "organization",
            "course",
            "document",
            "title",
            "description",
            "type",
            "difficulty",
            "time_limit_minutes",
            "passing_score_percentage",
            "status",
        ]
        read_only_fields = ["id"]


class QuizGenerateRequestSerializer(serializers.Serializer):
    """Payload to trigger AI generation of QCM questions."""

    count = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=20,
        help_text="Nombre de questions à générer",
    )
    document_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        default=None,
        help_text="UUID optionnel du document source",
    )
    provider = serializers.CharField(
        required=False,
        default=None,
        allow_null=True,
        help_text="Fournisseur IA (mock, openai, anthropic, gemini, local)",
    )
    model = serializers.CharField(
        required=False,
        default=None,
        allow_null=True,
        help_text="Modèle spécifique LLM",
    )
    focus = serializers.CharField(
        required=False,
        default=None,
        allow_null=True,
        allow_blank=True,
        help_text="Directive ou chapitre ciblé",
    )
    top_k = serializers.IntegerField(
        required=False,
        default=8,
        min_value=1,
        max_value=25,
        help_text="Nombre d'extraits RAG à analyser",
    )
    language = serializers.CharField(
        required=False,
        default=None,
        allow_null=True,
        allow_blank=True,
        help_text="Langue cible pour la génération (fr, ar, en)",
    )


class QuizSubmitPayloadSerializer(serializers.Serializer):
    """Payload submitted by user when answering a quiz."""

    answers = serializers.DictField(
        child=serializers.CharField(),
        required=True,
        help_text="Dictionnaire associant l'UUID de la question à l'UUID de la réponse choisie : {question_id: answer_id}",
    )


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Full serialization of a user attempt session."""

    quiz_title = serializers.CharField(source="quiz.title", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "quiz_title",
            "user",
            "user_email",
            "score",
            "total_questions",
            "correct_answers_count",
            "passed",
            "answers_data",
            "started_at",
            "completed_at",
            "time_spent_seconds",
        ]
        read_only_fields = fields
