import uuid

from django.db import models

from apps.courses.models import Course, CourseSection


class AudioStatus(models.TextChoices):
    PENDING = "PENDING", "En attente"
    PROCESSING = "PROCESSING", "En cours de génération"
    COMPLETED = "COMPLETED", "Généré"
    FAILED = "FAILED", "Échoué"


class AudioContent(models.Model):
    """Audio content synthesized from course lessons/sections via TTS."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="audio_contents",
        verbose_name="Cours associé",
        db_index=True,
    )
    section = models.ForeignKey(
        CourseSection,
        on_delete=models.CASCADE,
        related_name="audio_contents",
        verbose_name="Section / Leçon associée",
        db_index=True,
    )
    language = models.CharField(
        max_length=10,
        default="fr",
        verbose_name="Langue de synthèse",
    )
    voice_provider = models.CharField(
        max_length=50,
        default="mock",
        verbose_name="Fournisseur TTS (mock, openai, elevenlabs)",
    )
    voice_id = models.CharField(
        max_length=100,
        default="alloy",
        verbose_name="Identifiant de la voix",
    )
    script = models.TextField(
        blank=True,
        default="",
        verbose_name="Script pédagogique lu par le TTS",
    )
    storage_key = models.CharField(
        max_length=512,
        blank=True,
        default="",
        verbose_name="Clé de stockage (chemin S3 / local)",
    )
    duration = models.FloatField(
        default=0.0,
        verbose_name="Durée en secondes",
    )
    status = models.CharField(
        max_length=20,
        choices=AudioStatus.choices,
        default=AudioStatus.PENDING,
        db_index=True,
        verbose_name="Statut de génération",
    )
    error_message = models.TextField(
        blank=True,
        default="",
        verbose_name="Message d'erreur",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        db_table = "audio_content"
        verbose_name = "Contenu audio"
        verbose_name_plural = "Contenus audio"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["course", "status"]),
            models.Index(fields=["section", "status"]),
        ]

    def __str__(self) -> str:
        return f"Audio {self.section.title} ({self.status}) - {self.duration}s"

    def get_audio_url(self) -> str | None:
        """Returns downloadable or streaming URL from configured storage service."""
        if not self.storage_key:
            return None
        from apps.documents.services.storage import get_storage_service

        return get_storage_service().get_url(self.storage_key)
