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

        progresses = list(LearningProgress.objects.filter(user=self.user, course=self.course))
        completed_count = sum(1 for p in progresses if p.is_completed or p.completion_percent >= 100.0)
        total_percent = sum(min(100.0, max(0.0, p.completion_percent)) for p in progresses)
        calculated = min(100.0, round(total_percent / total_sections, 1))

        self.progress = calculated
        if (completed_count == total_sections and total_sections > 0) or self.progress >= 100.0:
            self.status = LearningPathStatus.COMPLETED
            if not self.completed_at:
                self.completed_at = timezone.now()
        elif self.progress > 0.0 or any(p.last_position > 0 for p in progresses):
            self.status = LearningPathStatus.IN_PROGRESS
            if not self.started_at:
                self.started_at = timezone.now()
            self.completed_at = None
        else:
            self.status = LearningPathStatus.NOT_STARTED
            self.completed_at = None

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
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Section déclarée terminée",
        db_index=True,
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de complétion",
    )
    last_viewed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Dernière consultation",
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
            models.Index(fields=["user", "is_completed"]),
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


class FlashcardDeck(models.Model):
    """Deck of flashcards generated from a Document or Course."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="flashcard_decks",
        verbose_name="Organisation",
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="flashcard_decks",
        verbose_name="Cours associé",
        db_index=True,
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="flashcard_decks",
        verbose_name="Document source",
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_flashcard_decks",
        verbose_name="Créateur",
    )
    title = models.CharField(max_length=255, verbose_name="Titre du paquet de fiches")
    description = models.TextField(blank=True, default="", verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")

    class Meta:
        db_table = "learning_flashcarddeck"
        verbose_name = "Paquet de fiches (Flashcards)"
        verbose_name_plural = "Paquets de fiches (Flashcards)"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} ({self.cards.count()} cartes)"


class Flashcard(models.Model):
    """Individual flashcard with question on front, answer on back, and optional hint."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deck = models.ForeignKey(
        FlashcardDeck,
        on_delete=models.CASCADE,
        related_name="cards",
        verbose_name="Paquet parent",
        db_index=True,
    )
    front = models.TextField(verbose_name="Question / Recto")
    back = models.TextField(verbose_name="Réponse / Verso")
    hint = models.CharField(max_length=255, blank=True, default="", verbose_name="Indice / Astuce mémo")
    source_citation = models.CharField(max_length=255, blank=True, default="", verbose_name="Citation source")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_flashcard"
        verbose_name = "Fiche mémo"
        verbose_name_plural = "Fiches mémo"
        ordering = ("order", "created_at")

    def __str__(self) -> str:
        return f"{self.deck.title} - Carte #{self.order}"


class FlashcardReview(models.Model):
    """Tracks spaced repetition state (SM-2 Algorithm) per user per card."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="flashcard_reviews",
        verbose_name="Apprenant",
        db_index=True,
    )
    card = models.ForeignKey(
        Flashcard,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Carte révisée",
        db_index=True,
    )
    repetitions = models.PositiveIntegerField(default=0, verbose_name="Répétitions consécutives réussies")
    ease_factor = models.FloatField(default=2.5, verbose_name="Facteur de facilité (EF)")
    interval_days = models.PositiveIntegerField(default=0, verbose_name="Intervalle en jours")
    last_quality = models.PositiveSmallIntegerField(default=0, verbose_name="Dernière note (0-5)")
    next_review_at = models.DateTimeField(default=timezone.now, verbose_name="Prochaine révision prévue", db_index=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Dernière révision")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "learning_flashcardreview"
        verbose_name = "État de révision espacée"
        verbose_name_plural = "États de révision espacée"
        unique_together = ("user", "card")
        indexes = [
            models.Index(fields=["user", "next_review_at"]),
        ]

    def record_review(self, quality: int):
        """Applies the SuperMemo-2 (SM-2) algorithm.

        quality: int from 0 to 5
        0-2: Recommencer la carte (échec)
        3-5: Réussite, espacement des intervalles
        """
        import datetime
        from django.utils import timezone

        q = max(0, min(5, quality))
        self.last_quality = q
        now = timezone.now()
        self.last_reviewed_at = now

        if q < 3:
            self.repetitions = 0
            self.interval_days = 1
        else:
            if self.repetitions == 0:
                self.interval_days = 1
            elif self.repetitions == 1:
                self.interval_days = 6
            else:
                self.interval_days = max(1, round(self.interval_days * self.ease_factor))
            self.repetitions += 1

        new_ef = self.ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        self.ease_factor = max(1.3, round(new_ef, 2))
        self.next_review_at = now + datetime.timedelta(days=self.interval_days)
        self.save(
            update_fields=[
                "repetitions",
                "ease_factor",
                "interval_days",
                "last_quality",
                "next_review_at",
                "last_reviewed_at",
                "updated_at",
            ]
        )
        return self

