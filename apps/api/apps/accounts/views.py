import logging

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    LoginSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """Register a new user account."""

    permission_classes = (AllowAny,)
    authentication_classes = ()

    @extend_schema(
        summary="User Registration",
        description="Creates a new user account and returns authentication tokens along with the user profile.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(
                description="Account created successfully",
                response={
                    "type": "object",
                    "properties": {
                        "user": {"type": "object"},
                        "access": {"type": "string"},
                        "refresh": {"type": "string"},
                    },
                },
            ),
            400: OpenApiResponse(description="Validation error"),
        },
        tags=["Authentication"],
    )
    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user, context={"request": request}).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate with email and password to receive JWT tokens."""

    permission_classes = (AllowAny,)
    authentication_classes = ()

    @extend_schema(
        summary="User Login",
        description="Authenticates credentials and returns JWT access and refresh tokens.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Authentication successful",
                response={
                    "type": "object",
                    "properties": {
                        "user": {"type": "object"},
                        "access": {"type": "string"},
                        "refresh": {"type": "string"},
                    },
                },
            ),
            400: OpenApiResponse(description="Invalid credentials or inactive account"),
        },
        tags=["Authentication"],
    )
    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        return Response(
            {
                "user": UserSerializer(user, context={"request": request}).data,
                "access": serializer.validated_data["access"],
                "refresh": serializer.validated_data["refresh"],
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Log out user and invalidate refresh token if provided."""

    permission_classes = (AllowAny,)

    @extend_schema(
        summary="User Logout",
        description="Terminates the active user session and optionally revokes the refresh token.",
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(
                description="Successfully logged out",
                response={
                    "type": "object",
                    "properties": {"detail": {"type": "string", "example": "Déconnexion réussie."}},
                },
            )
        },
        tags=["Authentication"],
    )
    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data.get("refresh")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (TokenError, AttributeError) as exc:
                logger.debug("Token blacklist notice: %s", exc)

        return Response(
            {"detail": "Déconnexion réussie."},
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    """Retrieve or update the authenticated user's profile."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Get Current User Profile",
        description="Returns profile information for the currently authenticated user.",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Unauthorized"),
        },
        tags=["Authentication"],
    )
    def get(self, request: Request) -> Response:
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update Current User Profile",
        description="Allows updating partial details (first_name, last_name, avatar, language).",
        request=UserUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Unauthorized"),
        },
        tags=["Authentication"],
    )
    def patch(self, request: Request) -> Response:
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )
