from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import Organization, OrganizationMember, RoleChoices

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    """Full representation of an Organization with caller role."""

    user_role = serializers.SerializerMethodField()
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "name",
            "slug",
            "logo",
            "plan",
            "user_role",
            "members_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "slug",
            "user_role",
            "members_count",
            "created_at",
            "updated_at",
        )

    def get_user_role(self, obj: Organization) -> str | None:
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.get_user_role(request.user)
        return None

    def get_members_count(self, obj: Organization) -> int:
        return obj.members.count()


class OrganizationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new Organization (caller becomes OWNER)."""

    class Meta:
        model = Organization
        fields = ("name", "plan", "logo")

    def create(self, validated_data: dict) -> Organization:
        request = self.context.get("request")
        user = request.user if request else None

        organization = Organization.objects.create(**validated_data)
        if user and user.is_authenticated:
            OrganizationMember.objects.create(
                organization=organization,
                user=user,
                role=RoleChoices.OWNER,
            )
        return organization


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating organization settings."""

    class Meta:
        model = Organization
        fields = ("name", "logo", "plan")


class OrganizationMemberSerializer(serializers.ModelSerializer):
    """Representation of an organization member."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = OrganizationMember
        fields = (
            "id",
            "organization",
            "user",
            "role",
            "created_at",
        )
        read_only_fields = (
            "id",
            "organization",
            "created_at",
        )


class OrganizationMemberCreateSerializer(serializers.Serializer):
    """Serializer for adding/inviting a member to an organization."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=[
            (RoleChoices.ADMIN, "Administrateur"),
            (RoleChoices.TEACHER, "Enseignant / Formateur"),
            (RoleChoices.STUDENT, "Apprenant / Étudiant"),
        ],
        default=RoleChoices.STUDENT,
    )

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Aucun utilisateur trouvé avec cette adresse email.")
        return email

    def validate(self, attrs: dict) -> dict:
        organization = self.context.get("organization")
        email = attrs.get("email")

        if organization:
            user = User.objects.get(email=email)
            if OrganizationMember.objects.filter(organization=organization, user=user).exists():
                raise serializers.ValidationError(
                    {"email": "Cet utilisateur est déjà membre de l'organisation."}
                )
        return attrs

    def create(self, validated_data: dict) -> OrganizationMember:
        organization = self.context["organization"]
        user = User.objects.get(email=validated_data["email"])
        role = validated_data.get("role", RoleChoices.STUDENT)

        return OrganizationMember.objects.create(
            organization=organization,
            user=user,
            role=role,
        )


class OrganizationMemberUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating member role."""

    class Meta:
        model = OrganizationMember
        fields = ("role",)

    def validate_role(self, value: str) -> str:
        instance = self.instance
        if instance and instance.role == RoleChoices.OWNER and value != RoleChoices.OWNER:
            raise serializers.ValidationError(
                "Le rôle du propriétaire ne peut être rétrogradé directement."
            )
        return value
