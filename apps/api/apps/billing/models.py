import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.organizations.models import Organization, PlanChoices


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Actif"
    TRIALING = "TRIALING", "Période d'essai"
    PAST_DUE = "PAST_DUE", "Paiement en attente"
    CANCELED = "CANCELED", "Annulé"


class UsageMetric(models.TextChoices):
    DOCUMENTS = "documents", "Documents importés"
    PAGES = "pages", "Pages analysées"
    STORAGE_BYTES = "storage", "Stockage consommé (octets)"
    AI_GENERATIONS = "ai_generations", "Générations IA"
    TOKENS = "tokens", "Jetons LLM consommés"
    AUDIO_MINUTES = "audio", "Minutes de synthèse audio"
    SLIDES = "slides", "Présentations générées"
    QUIZZES = "quizzes", "QCM & Examens créés"


class ReservationStatus(models.TextChoices):
    PENDING = "PENDING", "Réservé (en attente)"
    COMMITTED = "COMMITTED", "Consommé et confirmé"
    RELEASED = "RELEASED", "Libéré / Annulé"
    TIMEOUT_UNCERTAIN = "TIMEOUT_UNCERTAIN", "Résultat fournisseur incertain"


# Configurable per-user daily limits (-1 means unlimited)
USER_DAILY_LIMITS: dict[str, dict[str, int]] = {
    PlanChoices.FREE: {
        "ai_generations": 5,
        "audio": 5,
        "slides": 5,
        "quizzes": 5,
    },
    PlanChoices.PRO: {
        "ai_generations": 100,
        "audio": 50,
        "slides": 50,
        "quizzes": 50,
    },
    PlanChoices.BUSINESS: {
        "ai_generations": 500,
        "audio": 200,
        "slides": 200,
        "quizzes": 200,
    },
    PlanChoices.ENTERPRISE: {
        "ai_generations": -1,
        "audio": -1,
        "slides": -1,
        "quizzes": -1,
    },
}


# Default Quota thresholds by plan (-1 means unlimited)
PLAN_QUOTAS: dict[str, dict[str, int]] = {
    PlanChoices.FREE: {
        "documents": 5,
        "pages": 50,
        "storage": 100 * 1024 * 1024,  # 100 MB
        "ai_generations": 10,
        "tokens": 50_000,
        "audio": 15,  # 15 minutes
        "slides": 20,
        "quizzes": 10,
    },
    PlanChoices.PRO: {
        "documents": 50,
        "pages": 1_000,
        "storage": 2 * 1024 * 1024 * 1024,  # 2 GB
        "ai_generations": 250,
        "tokens": 1_000_000,
        "audio": 180,  # 3 hours
        "slides": 200,
        "quizzes": 100,
    },
    PlanChoices.BUSINESS: {
        "documents": 250,
        "pages": 10_000,
        "storage": 20 * 1024 * 1024 * 1024,  # 20 GB
        "ai_generations": 2_500,
        "tokens": 10_000_000,
        "audio": 1_200,  # 20 hours
        "slides": 1_000,
        "quizzes": 1_000,
    },
    PlanChoices.ENTERPRISE: {
        "documents": -1,
        "pages": -1,
        "storage": -1,
        "ai_generations": -1,
        "tokens": -1,
        "audio": -1,
        "slides": -1,
        "quizzes": -1,
    },
}


class Subscription(models.Model):
    """Organization subscription contract tracking active plan and billing status."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="subscription",
        verbose_name="Organisation abonnée",
        db_index=True,
    )
    plan = models.CharField(
        max_length=30,
        choices=PlanChoices.choices,
        default=PlanChoices.FREE,
        verbose_name="Plan souscrit",
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
        verbose_name="Statut de l'abonnement",
        db_index=True,
    )
    started_at = models.DateTimeField(default=timezone.now, verbose_name="Début de la période")
    current_period_end = models.DateTimeField(
        null=True, blank=True, verbose_name="Fin de la période"
    )
    canceled_at = models.DateTimeField(null=True, blank=True, verbose_name="Date d'annulation")
    billing_provider = models.CharField(
        max_length=50, default="mock", verbose_name="Fournisseur de facturation"
    )
    provider_customer_id = models.CharField(
        max_length=255, blank=True, default="", verbose_name="ID Client externe"
    )
    provider_subscription_id = models.CharField(
        max_length=255, blank=True, default="", verbose_name="ID Abonnement externe"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        db_table = "billing_subscription"
        verbose_name = "Abonnement"
        verbose_name_plural = "Abonnements"

    def __str__(self) -> str:
        return f"{self.organization.name} - {self.get_plan_display()} ({self.status})"

    def is_active(self) -> bool:
        return self.status in (SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING)

    def get_quota(self, metric: str) -> int:
        quotas = PLAN_QUOTAS.get(self.plan, PLAN_QUOTAS[PlanChoices.FREE])
        return quotas.get(metric, 0)


class UsageRecord(models.Model):
    """Tracks actual resource consumption for an organization."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="usage_records",
        verbose_name="Organisation",
        db_index=True,
    )
    metric = models.CharField(
        max_length=50,
        choices=UsageMetric.choices,
        verbose_name="Métrique suivie",
        db_index=True,
    )
    quantity = models.BigIntegerField(default=0, verbose_name="Quantité consommée")
    period_start = models.DateTimeField(default=timezone.now, verbose_name="Début du cycle")
    period_end = models.DateTimeField(null=True, blank=True, verbose_name="Fin du cycle")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        db_table = "billing_usagerecord"
        verbose_name = "Enregistrement de consommation"
        verbose_name_plural = "Enregistrements de consommation"
        unique_together = ("organization", "metric")
        indexes = [
            models.Index(fields=["organization", "metric"]),
        ]

    def __str__(self) -> str:
        return f"{self.organization.name} - {self.metric}: {self.quantity}"


class AuditLog(models.Model):
    """Immutable audit trail for security compliance, administrative actions, and traceability."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name="Organisation",
        db_index=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_actions",
        verbose_name="Utilisateur initiateur",
        db_index=True,
    )
    action = models.CharField(max_length=100, verbose_name="Action réalisée", db_index=True)
    resource_type = models.CharField(
        max_length=100, verbose_name="Type de ressource", db_index=True
    )
    resource_id = models.CharField(
        max_length=255, blank=True, default="", verbose_name="Identifiant ressource"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adresse IP")
    user_agent = models.TextField(blank=True, default="", verbose_name="User Agent")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Données contextuelles")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Horodatage", db_index=True)

    class Meta:
        db_table = "billing_auditlog"
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self) -> str:
        actor_name = self.actor.email if self.actor else "Système"
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {actor_name} -> {self.action} ({self.resource_type})"


class QuotaReservation(models.Model):
    """Tracks two-phase quota reservations to guarantee atomic consistency under concurrency.

    Prevents race conditions, handles task retries via idempotency key,
    and isolates pending, committed, and refunded resource consumptions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="quota_reservations",
        verbose_name="Organisation",
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quota_reservations",
        verbose_name="Utilisateur initiateur",
        db_index=True,
    )
    metric = models.CharField(
        max_length=50,
        choices=UsageMetric.choices,
        verbose_name="Métrique réservée",
        db_index=True,
    )
    reserved_amount = models.BigIntegerField(default=1, verbose_name="Quantité réservée")
    actual_amount = models.BigIntegerField(
        null=True, blank=True, verbose_name="Quantité confirmée consommée"
    )
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        verbose_name="Clé d'idempotence",
    )
    task_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        verbose_name="ID de tâche Celery",
    )
    status = models.CharField(
        max_length=30,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
        db_index=True,
        verbose_name="Statut de la réservation",
    )
    estimated_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0.0,
        verbose_name="Coût estimé (USD)",
    )
    actual_cost_usd = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Coût réel confirmé (USD)",
    )
    is_cost_estimated = models.BooleanField(
        default=True,
        verbose_name="Coût estimatif (non confirmé par fournisseur)",
    )
    error_detail = models.TextField(
        blank=True,
        default="",
        verbose_name="Détail d'anomalie ou timeout",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Réservé le", db_index=True)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        db_table = "billing_quotareservation"
        verbose_name = "Réservation de quota"
        verbose_name_plural = "Réservations de quotas"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["organization", "metric", "status"]),
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["idempotency_key"]),
        ]

    def __str__(self) -> str:
        return f"[{self.status}] Org {self.organization_id} - {self.metric}: {self.reserved_amount} (Key: {self.idempotency_key})"
