import uuid

from django.db import models

from apps.courses.models import Course


class PresentationTheme(models.TextChoices):
    MODERN_DARK = "modern_dark", "Moderne Sombre"
    MINIMAL_LIGHT = "minimal_light", "Minimaliste Clair"
    ACADEMIC_INDIGO = "academic_indigo", "Académique Indigo"
    CORPORATE_BLUE = "corporate_blue", "Entreprise Bleu"


class PresentationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Brouillon"
    GENERATING = "GENERATING", "En cours de génération"
    READY = "READY", "Prêt"
    EXPORTING = "EXPORTING", "Exportation en cours"
    FAILED = "FAILED", "Échec"


class Presentation(models.Model):
    """Pedagogical slide deck generated from a Course."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="presentations",
        verbose_name="Cours source",
        db_index=True,
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Titre de la présentation",
    )
    theme = models.CharField(
        max_length=50,
        choices=PresentationTheme.choices,
        default=PresentationTheme.MODERN_DARK,
        verbose_name="Thème graphique",
    )
    status = models.CharField(
        max_length=20,
        choices=PresentationStatus.choices,
        default=PresentationStatus.DRAFT,
        verbose_name="Statut",
        db_index=True,
    )
    storage_key = models.CharField(
        max_length=512,
        blank=True,
        default="",
        verbose_name="Clé de stockage du fichier PPTX exporté",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        db_table = "slides_presentation"
        verbose_name = "Présentation"
        verbose_name_plural = "Présentations"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["course", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_theme_display()})"

    def get_export_url(self) -> str | None:
        """Returns downloadable URL for the exported PPTX file."""
        if not self.storage_key:
            return None
        from apps.documents.services.storage import get_storage_service

        return get_storage_service().get_url(self.storage_key)


class PresentationSlide(models.Model):
    """Individual slide within a Presentation deck."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    presentation = models.ForeignKey(
        Presentation,
        on_delete=models.CASCADE,
        related_name="slides",
        verbose_name="Présentation parente",
        db_index=True,
    )
    slide_number = models.PositiveIntegerField(
        default=1,
        verbose_name="Numéro d'ordre de la slide",
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Titre de la slide",
    )
    content = models.TextField(
        blank=True,
        default="",
        verbose_name="Contenu didactique (puces, points clés)",
    )
    speaker_notes = models.TextField(
        blank=True,
        default="",
        verbose_name="Notes de l'orateur / Présentateur",
    )
    image_prompt = models.TextField(
        blank=True,
        default="",
        verbose_name="Prompt visuel / Idée d'illustration",
    )
    image_url = models.URLField(
        max_length=1024,
        blank=True,
        default="",
        verbose_name="URL de l'image d'illustration",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        db_table = "slides_presentationslide"
        verbose_name = "Slide de présentation"
        verbose_name_plural = "Slides de présentation"
        ordering = ("slide_number", "created_at")
        indexes = [
            models.Index(fields=["presentation", "slide_number"]),
        ]

    def __str__(self) -> str:
        return f"Slide {self.slide_number} : {self.title}"
