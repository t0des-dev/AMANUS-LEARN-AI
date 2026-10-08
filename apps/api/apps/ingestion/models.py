import uuid

from django.db import models
from pgvector.django import VectorField


class DocumentPage(models.Model):
    """Represents an extracted page, slide, or logical segment of a document."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="pages",
        verbose_name="Document",
        db_index=True,
    )
    page_number = models.PositiveIntegerField(
        verbose_name="Numéro de page / slide",
        help_text="Numérotation 1-indexée de la page",
    )
    text = models.TextField(
        blank=True,
        default="",
        verbose_name="Texte extrait",
    )
    ocr_used = models.BooleanField(
        default=False,
        verbose_name="OCR utilisé",
        help_text="Indique si le moteur OCR a été sollicité pour cette page",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées de la page",
        help_text="Dimensions, orientation, chapitres détectés, confiance OCR, etc.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'extraction",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de mise à jour",
    )

    class Meta:
        db_table = "ingestion_documentpage"
        verbose_name = "Page de document"
        verbose_name_plural = "Pages de documents"
        unique_together = (("document", "page_number"),)
        ordering = ("page_number",)
        indexes = [
            models.Index(fields=["document", "page_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.document.title} - Page {self.page_number}"


class DocumentChunk(models.Model):
    """Represents a text chunk derived from a document, ready for embedding and RAG indexing."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.CASCADE,
        related_name="chunks",
        verbose_name="Document",
        db_index=True,
    )
    page = models.ForeignKey(
        DocumentPage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chunks",
        verbose_name="Page d'origine",
    )
    chunk_index = models.PositiveIntegerField(
        verbose_name="Index du chunk",
        help_text="Ordre séquentiel du chunk dans le document",
    )
    content = models.TextField(
        verbose_name="Contenu textuel du chunk",
    )
    token_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Nombre de tokens estimés",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées contextuelles",
        help_text="Préserve document, page, chapitre, section, sous-section, etc.",
    )
    embedding = VectorField(
        dimensions=1536,
        null=True,
        blank=True,
        verbose_name="Embedding vectoriel",
        help_text="Vecteur pgvector réservé pour l'indexation IA",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de mise à jour",
    )

    class Meta:
        db_table = "ingestion_documentchunk"
        verbose_name = "Chunk de document"
        verbose_name_plural = "Chunks de documents"
        ordering = ("chunk_index",)
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
            models.Index(fields=["document", "page"]),
        ]

    def __str__(self) -> str:
        return f"{self.document.title} - Chunk #{self.chunk_index} ({self.token_count} tok)"
