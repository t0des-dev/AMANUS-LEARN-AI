import uuid

from django.conf import settings
from django.db import models


class CourseLevel(models.TextChoices):
    BEGINNER = "BEGINNER", "Débutant"
    INTERMEDIATE = "INTERMEDIATE", "Intermédiaire"
    ADVANCED = "ADVANCED", "Avancé"
    EXPERT = "EXPERT", "Expert"


class CourseStatus(models.TextChoices):
    DRAFT = "DRAFT", "Brouillon"
    PUBLISHED = "PUBLISHED", "Publié"
    ARCHIVED = "ARCHIVED", "Archivé"


class Course(models.Model):
    """Pedagogical course entity transformed from ingested documents or built manually."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="Organisation",
        db_index=True,
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses",
        verbose_name="Document source",
        db_index=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_courses",
        verbose_name="Créateur",
    )
    title = models.CharField(max_length=255, verbose_name="Titre du cours")
    description = models.TextField(blank=True, default="", verbose_name="Description")
    language = models.CharField(max_length=10, default="fr", verbose_name="Langue")
    level = models.CharField(
        max_length=20,
        choices=CourseLevel.choices,
        default=CourseLevel.BEGINNER,
        verbose_name="Niveau",
    )
    status = models.CharField(
        max_length=20,
        choices=CourseStatus.choices,
        default=CourseStatus.DRAFT,
        verbose_name="Statut",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")

    class Meta:
        db_table = "courses_course"
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"


class CourseSection(models.Model):
    """Hierarchical course component representing Chapter, Section, or Lesson.

    Hierarchy is preserved through the recursive 'parent' relation:
    - parent is None -> Chapter (Level 1)
    - parent is Chapter -> Section (Level 2)
    - parent is Section -> Lesson (Level 3)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="Cours parent",
        db_index=True,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Section parente (Chapitre ou Section)",
        db_index=True,
    )
    title = models.CharField(max_length=255, verbose_name="Titre de la section")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")
    content = models.TextField(
        blank=True,
        default="",
        verbose_name="Contenu didactique (éditable par l'enseignant)",
    )
    summary = models.TextField(blank=True, default="", verbose_name="Synthèse / Résumé")
    objectives = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Objectifs pédagogiques",
    )
    estimated_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name="Durée estimée (minutes)",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")

    class Meta:
        db_table = "courses_coursesection"
        verbose_name = "Section de cours"
        verbose_name_plural = "Sections de cours"
        ordering = ["order", "created_at"]

    def __str__(self) -> str:
        return f"{self.title} (Ordre: {self.order})"

    @property
    def level_depth(self) -> int:
        """Returns 0 for root chapter, 1 for section, 2 for lesson."""
        depth = 0
        current = self.parent
        while current is not None:
            depth += 1
            current = current.parent
        return depth
