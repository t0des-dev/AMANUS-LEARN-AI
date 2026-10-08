import uuid

from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class ChatSession(models.Model):
    """Conversational pedagogical session linking a user and an organization.

    Can optionally be scoped to a specific document or course.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
        verbose_name="Organisation",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
        verbose_name="Utilisateur",
        db_index=True,
    )
    title = models.CharField(
        max_length=255,
        default="Nouvelle session pédagogique",
        verbose_name="Titre de la session",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_sessions",
        verbose_name="Document d'ancrage",
        db_index=True,
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chat_sessions",
        verbose_name="Cours d'ancrage",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        db_table = "chat_session"
        verbose_name = "Session de chat"
        verbose_name_plural = "Sessions de chat"
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["organization", "user", "-updated_at"]),
            models.Index(fields=["user", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.user})"


class MessageRole(models.TextChoices):
    USER = "user", "Utilisateur"
    ASSISTANT = "assistant", "Assistant / Tuteur"
    SYSTEM = "system", "Système"


class ChatMessage(models.Model):
    """Individual message within a pedagogical ChatSession."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Session",
        db_index=True,
    )
    role = models.CharField(
        max_length=20,
        choices=MessageRole.choices,
        default=MessageRole.USER,
        verbose_name="Rôle",
    )
    content = models.TextField(verbose_name="Contenu du message")
    command = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Commande pédagogique",
        help_text="EXPLAIN, SIMPLIFY, SUMMARY, EXAMPLE, QUIZ, REVISION, COMPARE, DEFINE",
    )
    sources = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Sources documentaires citées",
    )
    tokens_used = models.PositiveIntegerField(
        default=0,
        verbose_name="Tokens consommés",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées d'inférence",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'envoi")

    class Meta:
        db_table = "chat_message"
        verbose_name = "Message de chat"
        verbose_name_plural = "Messages de chat"
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=["session", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.role}] {self.content[:50]}"

    @property
    def sender(self) -> str:
        """Alias for compatibility with sender representation."""
        return self.role
