import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.courses.models import Course, CourseSection


class LearningPathStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", "Non démarré"
    IN_PROGRESS = "IN_PROGRESS", "En cours"
    COMPLETED = "COMPLETED", "Terminé"


class LearningPath(models.Model):
    """Tracks a user's enrollment and overall progression in a Course."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learning_paths",
        verbose_name="Apprenant",
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="learning_paths",
        verbose_name="Cours suivi",
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=LearningPathStatus.choices,
        default=LearningPathStatus.NOT_STARTED,
        verbose_name="Statut d'apprentissage",
        db_index=True,
    )
    progress = models.FloatField(
        default=0.0,
        verbose_name="Progression globale (%)",
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de début d'apprentissage",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'achèvement",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière activité")

    class Meta:
        db_table = "learning_learningpath"
        verbose_name = "Parcours d'apprentissage"
        verbose_name_plural = "Parcours d'apprentissage"
        unique_together = ("user", "course")
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["user", "course"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.course.title} ({self.progress:.1f}%)"

    def recalculate_progress(self) -> float:
        """Calculates global course completion percentage from section records."""
        sections = self.course.sections.all()
        total_sections = sections.count()

        if total_sections == 0:
            self.progress = 100.0
            self.status = LearningPathStatus.COMPLETED
            if not self.completed_at:
                self.completed_at = timezone.now()
            self.save(update_fields=["progress", "status", "completed_at", "updated_at"])
            return 100.0

        progresses = LearningProgress.objects.filter(user=self.user, course=self.course)
        total_percent = sum(p.completion_percent for p in progresses)
        calculated = min(100.0, round(total_percent / total_sections, 1))

        self.progress = calculated
        if self.progress >= 100.0:
            self.status = LearningPathStatus.COMPLETED
            if not self.completed_at:
                self.completed_at = timezone.now()
        elif self.progress > 0.0:
            self.status = LearningPathStatus.IN_PROGRESS
            if not self.started_at:
                self.started_at = timezone.now()
        else:
            self.status = LearningPathStatus.NOT_STARTED

        self.save(update_fields=["progress", "status", "started_at", "completed_at", "updated_at"])
        return self.progress


class LearningProgress(models.Model):
    """Tracks a user's granular progress and performance on a specific CourseSection."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learning_progresses",
        verbose_name="Apprenant",
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="learning_progresses",
        verbose_name="Cours",
        db_index=True,
    )
    section = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name="learning_progresses",
        verbose_name="Section / Chapitre",
        db_index=True,
    )
    completion_percent = models.FloatField(
        default=0.0,
        verbose_name="Progression de la section (%)",
    )
    last_position = models.IntegerField(
        default=0,
        verbose_name="Dernière position de lecture / défilement",
    )
    score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Score de maîtrise / Quiz (%)",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière activité")

    class Meta:
        db_table = "learning_learningprogress"
        verbose_name = "Progression de section"
        verbose_name_plural = "Progressions de section"
        unique_together = ("user", "section")
        ordering = ("section__order", "created_at")
        indexes = [
            models.Index(fields=["user", "course"]),
            models.Index(fields=["user", "section"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.section.title}: {self.completion_percent:.0f}%"


class StudySession(models.Model):
    """Tracks dedicated time spent by a student studying a course."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_sessions",
        verbose_name="Apprenant",
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="study_sessions",
        verbose_name="Cours étudié",
        db_index=True,
    )
    started_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Début de la session",
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fin de la session",
    )
    duration = models.PositiveIntegerField(
        default=0,
        verbose_name="Durée en secondes",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        db_table = "learning_studysession"
        verbose_name = "Session d'étude"
        verbose_name_plural = "Sessions d'étude"
        ordering = ("-started_at",)
        indexes = [
            models.Index(fields=["user", "course"]),
            models.Index(fields=["user", "started_at"]),
        ]

    def __str__(self) -> str:
        return f"Session {self.user} sur {self.course.title} ({self.duration}s)"

    def finish(self) -> int:
        """Closes the session, calculates duration in seconds and persists."""
        if not self.ended_at:
            self.ended_at = timezone.now()
        diff = (self.ended_at - self.started_at).total_seconds()
        self.duration = max(0, int(diff))
        self.save(update_fields=["ended_at", "duration", "updated_at"])
        return self.duration
