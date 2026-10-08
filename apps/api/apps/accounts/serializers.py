from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Public profile representation of the User."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "language",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "email",
            "is_active",
            "created_at",
            "updated_at",
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile information."""

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "avatar",
            "language",
        )


class RegisterSerializer(serializers.Serializer):
    """Serializer for self-service user registration."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=False, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, default="")
    last_name = serializers.CharField(required=False, allow_blank=True, default="")
    language = serializers.CharField(required=False, default="fr", max_length=10)

    def validate_email(self, value: str) -> str:
        email = value.strip().lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("Un compte existe déjà avec cette adresse email.")
        return email

    def validate(self, attrs: dict) -> dict:
        password = attrs.get("password")
        password_confirm = attrs.get("password_confirm")

        if password_confirm is not None and password != password_confirm:
            raise serializers.ValidationError(
                {"password_confirm": "Les mots de passe ne correspondent pas."}
            )

        validate_password(password)
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop("password_confirm", None)
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer for authenticating users via email & password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password", "")

        if not email or not password:
            raise serializers.ValidationError("Veuillez renseigner un email et un mot de passe.")

        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=password,
        )

        if not user:
            # Check if user exists but inactive
            existing_user = User.objects.filter(email=email).first()
            if existing_user and not existing_user.is_active:
                raise serializers.ValidationError(
                    {"detail": "Ce compte utilisateur est désactivé."}
                )
            raise serializers.ValidationError({"detail": "Identifiants de connexion invalides."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "Ce compte utilisateur est désactivé."})

        refresh = RefreshToken.for_user(user)

        return {
            "user": user,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class LogoutSerializer(serializers.Serializer):
    """Serializer for logging out and optional token revocation."""

    refresh = serializers.CharField(required=False, allow_blank=True)
