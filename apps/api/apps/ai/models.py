import uuid

from django.conf import settings
from django.db import models


class GenerationType(models.TextChoices):
    SUMMARY = "SUMMARY", "Résumé"
    KEY_POINTS = "KEY_POINTS", "Points clés"
    OBJECTIVES = "OBJECTIVES", "Objectifs pédagogiques"
    LESSON = "LESSON", "Cours / Leçon"
    REVISION_SHEET = "REVISION_SHEET", "Fiche de révision"


class GenerationStatus(models.TextChoices):
    PENDING = "PENDING", "En cours"
    SUCCESS = "SUCCESS", "Succès"
    FAILED = "FAILED", "Échec"


class AIGeneration(models.Model):
    """Stores full audit logs and content for every AI generation event."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name="generations",
        verbose_name="Organisation",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generations",
        verbose_name="Utilisateur",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="generations",
        verbose_name="Document source",
        db_index=True,
    )
    type = models.CharField(
        max_length=50,
        choices=GenerationType.choices,
        verbose_name="Type de génération",
        db_index=True,
    )
    provider = models.CharField(
        max_length=50,
        verbose_name="Fournisseur IA (openai, anthropic, gemini, local, mock)",
    )
    model = models.CharField(
        max_length=100,
        verbose_name="Modèle LLM utilisé",
    )
    prompt_version = models.CharField(
        max_length=20,
        default="v1.0",
        verbose_name="Version du prompt",
    )
    input_tokens = models.PositiveIntegerField(
        default=0,
        verbose_name="Tokens d'entrée",
    )
    output_tokens = models.PositiveIntegerField(
        default=0,
        verbose_name="Tokens de sortie",
    )
    status = models.CharField(
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.PENDING,
        db_index=True,
        verbose_name="Statut de la génération",
    )
    result = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Résultat structuré",
    )
    error = models.TextField(
        blank=True,
        default="",
        verbose_name="Message d'erreur",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de génération",
    )

    class Meta:
        db_table = "ai_generation"
        verbose_name = "Génération IA"
        verbose_name_plural = "Générations IA"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["organization", "type"]),
            models.Index(fields=["document", "type"]),
            models.Index(fields=["organization", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.type} ({self.provider}/{self.model}) - {self.status}"
