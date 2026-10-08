import uuid

from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class DocumentStatus(models.TextChoices):
    """Lifecycle statuses for document processing."""

    UPLOADING = "UPLOADING", "Uploading"
    UPLOADED = "UPLOADED", "Uploadé"
    EXTRACTING = "EXTRACTING", "Extracting"
    OCR = "OCR", "OCR"
    STRUCTURING = "STRUCTURING", "Structuring"
    CHUNKING = "CHUNKING", "Chunking"
    PROCESSING = "PROCESSING", "En cours de traitement"
    COMPLETED = "COMPLETED", "Completed"
    READY = "READY", "Prêt"
    FAILED = "FAILED", "Échoué"
    ARCHIVED = "ARCHIVED", "Archivé"


class Document(models.Model):
    """Document model representing imported educational or professional material."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Organisation",
        db_index=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name="Propriétaire / Auteur",
    )
    title = models.CharField(max_length=255, verbose_name="Titre du document")
    description = models.TextField(blank=True, default="", verbose_name="Description")
    file_name = models.CharField(max_length=255, verbose_name="Nom du fichier original")
    file_type = models.CharField(
        max_length=50,
        verbose_name="Format du fichier (pdf, docx, pptx, txt)",
    )
    file_size = models.PositiveBigIntegerField(
        help_text="Taille en octets",
        verbose_name="Taille du fichier",
    )
    storage_key = models.CharField(
        max_length=512,
        unique=True,
        verbose_name="Clé de stockage (chemin S3 / local)",
    )
    language = models.CharField(
        max_length=10,
        default="fr",
        verbose_name="Langue principale du document",
    )
    page_count = models.PositiveIntegerField(
        default=0,
        null=True,
        blank=True,
        verbose_name="Nombre de pages estimé",
    )
    status = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.UPLOADED,
        db_index=True,
        verbose_name="Statut du document",
    )
    error_message = models.TextField(
        blank=True,
        default="",
        verbose_name="Message d'erreur",
    )
    processing_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées du pipeline",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'importation")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")

    class Meta:
        db_table = "documents_document"
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.organization.name})"

    @property
    def file_extension(self) -> str:
        """Returns normalized file extension starting with a dot."""
        if "." in self.file_name:
            return "." + self.file_name.rsplit(".", 1)[-1].lower()
        return f".{self.file_type.lower()}"

    @property
    def file_size_human(self) -> str:
        """Returns human-readable representation of file size."""
        bytes_val = float(self.file_size)
        for unit in ["o", "Ko", "Mo", "Go"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} To"

    def get_download_url(self) -> str:
        """Generate download URL from the configured storage service."""
        from .services.storage import get_storage_service

        return get_storage_service().get_url(self.storage_key)
