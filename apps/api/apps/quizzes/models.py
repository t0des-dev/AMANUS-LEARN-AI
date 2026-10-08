import uuid

from django.conf import settings
from django.db import models


class QuizType(models.TextChoices):
    TRAINING = "TRAINING", "Entraînement"
    EXAM = "EXAM", "Examen"
    REVISION = "REVISION", "Révision"


class DifficultyLevel(models.TextChoices):
    EASY = "EASY", "Facile"
    MEDIUM = "MEDIUM", "Moyen"
    HARD = "HARD", "Difficile"


class QuizStatus(models.TextChoices):
    DRAFT = "DRAFT", "Brouillon"
    PUBLISHED = "PUBLISHED", "Publié"
    ARCHIVED = "ARCHIVED", "Archivé"


class Quiz(models.Model):
    """Quiz / QCM entity linked to an organization, course, or analyzed document."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="quizzes",
        verbose_name="Organisation",
        db_index=True,
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quizzes",
        verbose_name="Cours associé",
        db_index=True,
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quizzes",
        verbose_name="Document source",
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_quizzes",
        verbose_name="Créateur",
    )
    title = models.CharField(max_length=255, verbose_name="Titre du QCM")
    description = models.TextField(blank=True, default="", verbose_name="Description")
    type = models.CharField(
        max_length=20,
        choices=QuizType.choices,
        default=QuizType.TRAINING,
        verbose_name="Mode de quiz",
        db_index=True,
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        verbose_name="Niveau de difficulté",
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name="Temps limite (minutes)",
    )
    passing_score_percentage = models.PositiveIntegerField(
        default=70,
        verbose_name="Score de validation (%)",
    )
    status = models.CharField(
        max_length=20,
        choices=QuizStatus.choices,
        default=QuizStatus.PUBLISHED,
        verbose_name="Statut",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")

    class Meta:
        db_table = "quizzes_quiz"
        verbose_name = "QCM / Quiz"
        verbose_name_plural = "QCM / Quiz"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_type_display()} - {self.get_difficulty_display()})"


class QuizQuestion(models.Model):
    """Multiple choice question with strict 4 options validation and explanation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Quiz parent",
        db_index=True,
    )
    text = models.TextField(verbose_name="Énoncé de la question")
    explanation = models.TextField(
        blank=True,
        default="",
        verbose_name="Explication pédagogique de la bonne réponse",
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        verbose_name="Difficulté de la question",
    )
    source = models.CharField(
        max_length=512,
        blank=True,
        default="",
        verbose_name="Source documentaire / Citation de référence",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        db_table = "quizzes_quizquestion"
        verbose_name = "Question de QCM"
        verbose_name_plural = "Questions de QCM"
        ordering = ["order", "created_at"]

    def __str__(self) -> str:
        return f"Q{self.order + 1}: {self.text[:50]}"


class QuizAnswer(models.Model):
    """Individual answer option for a QuizQuestion. Exactly one option must be correct."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        QuizQuestion,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Question parente",
        db_index=True,
    )
    text = models.CharField(max_length=512, verbose_name="Texte de l'option de réponse")
    is_correct = models.BooleanField(
        default=False,
        verbose_name="Est la bonne réponse",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")

    class Meta:
        db_table = "quizzes_quizanswer"
        verbose_name = "Option de réponse"
        verbose_name_plural = "Options de réponse"
        ordering = ["order"]

    def __str__(self) -> str:
        return f"{self.text[:30]} ({'Correct' if self.is_correct else 'Faux'})"


class QuizAttempt(models.Model):
    """User attempt session tracking time, choices, score, and pass/fail evaluation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Quiz tenté",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
        verbose_name="Apprenant",
        db_index=True,
    )
    score = models.FloatField(
        default=0.0,
        verbose_name="Score obtenu (%)",
    )
    total_questions = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre total de questions",
    )
    correct_answers_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de bonnes réponses",
    )
    passed = models.BooleanField(
        default=False,
        verbose_name="Réussi (seuil atteint)",
    )
    answers_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Données des réponses soumises {question_id: answer_id}",
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Début de la tentative",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fin de la tentative",
    )
    time_spent_seconds = models.PositiveIntegerField(
        default=0,
        verbose_name="Temps passé (secondes)",
    )

    class Meta:
        db_table = "quizzes_quizattempt"
        verbose_name = "Tentative de QCM"
        verbose_name_plural = "Tentatives de QCM"
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Tentative {self.user.email} sur {self.quiz.title} : {self.score}%"
