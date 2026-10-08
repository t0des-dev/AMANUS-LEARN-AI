import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class PlanChoices(models.TextChoices):
    FREE = "FREE", "Gratuit"
    PRO = "PRO", "Professionnel"
    BUSINESS = "BUSINESS", "Business"
    ENTERPRISE = "ENTERPRISE", "Entreprise"


class RoleChoices(models.TextChoices):
    OWNER = "OWNER", "Propriétaire"
    ADMIN = "ADMIN", "Administrateur"
    TEACHER = "TEACHER", "Enseignant / Formateur"
    STUDENT = "STUDENT", "Apprenant / Étudiant"


class Organization(models.Model):
    """Multi-tenant Organization entity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name="Nom de l'organisation")
    slug = models.SlugField(max_length=220, unique=True, db_index=True)
    logo = models.ImageField(
        upload_to="organizations/logos/",
        null=True,
        blank=True,
        verbose_name="Logo",
    )
    plan = models.CharField(
        max_length=30,
        choices=PlanChoices.choices,
        default=PlanChoices.FREE,
        verbose_name="Plan d'abonnement",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de modification")

    class Meta:
        db_table = "organizations_organization"
        verbose_name = "Organisation"
        verbose_name_plural = "Organisations"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "org"
            slug = base_slug
            counter = 1
            while Organization.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_user_role(self, user) -> str | None:
        if not user or not user.is_authenticated:
            return None
        membership = self.members.filter(user=user).first()
        return membership.role if membership else None

    def is_member(self, user) -> bool:
        if not user or not user.is_authenticated:
            return False
        return self.members.filter(user=user).exists()

    def is_owner(self, user) -> bool:
        return self.get_user_role(user) == RoleChoices.OWNER

    def is_admin_or_owner(self, user) -> bool:
        return self.get_user_role(user) in (RoleChoices.OWNER, RoleChoices.ADMIN)


class OrganizationMember(models.Model):
    """Membership linking Users to Organizations with specific roles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="members",
        verbose_name="Organisation",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
        verbose_name="Utilisateur",
    )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.STUDENT,
        verbose_name="Rôle",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date d'adhésion")

    class Meta:
        db_table = "organizations_member"
        verbose_name = "Membre d'organisation"
        verbose_name_plural = "Membres d'organisation"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="unique_organization_member",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} - {self.organization} ({self.role})"
