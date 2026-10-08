from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    get_object_or_404,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Organization, OrganizationMember, RoleChoices
from .serializers import (
    OrganizationCreateSerializer,
    OrganizationMemberCreateSerializer,
    OrganizationMemberSerializer,
    OrganizationMemberUpdateSerializer,
    OrganizationSerializer,
    OrganizationUpdateSerializer,
)


class OrganizationListCreateView(ListCreateAPIView):
    """
    List user's organizations or create a new one.
    Strict tenant isolation: only organizations where the user is a member are returned.
    """

    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Organization.objects.filter(members__user=self.request.user)
            .distinct()
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrganizationCreateSerializer
        return OrganizationSerializer

    @extend_schema(
        summary="List User Organizations",
        description="Returns all organizations the current authenticated user belongs to.",
        responses={200: OrganizationSerializer(many=True)},
        tags=["Organizations"],
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create Organization",
        description="Creates a new multi-tenant organization. The creator automatically receives the OWNER role.",
        request=OrganizationCreateSerializer,
        responses={201: OrganizationSerializer},
        tags=["Organizations"],
    )
    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()
        return Response(
            OrganizationSerializer(organization, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationDetailView(RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an organization.
    Multi-tenant isolation: user must belong to the organization.
    """

    permission_classes = (IsAuthenticated,)
    lookup_field = "id"
    lookup_url_kwarg = "id"

    def get_queryset(self):
        return Organization.objects.filter(members__user=self.request.user).distinct()

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return OrganizationUpdateSerializer
        return OrganizationSerializer

    def check_object_permissions(self, request: Request, obj: Organization):
        super().check_object_permissions(request, obj)
        if request.method in ("PUT", "PATCH"):
            if not obj.is_admin_or_owner(request.user):
                raise PermissionDenied(
                    "Seuls les propriétaires et administrateurs peuvent modifier cette organisation."
                )
        elif request.method == "DELETE":
            if not obj.is_owner(request.user):
                raise PermissionDenied("Seul le propriétaire peut supprimer cette organisation.")

    @extend_schema(
        summary="Get Organization Details",
        description="Returns details for a specific organization if the user is a member.",
        responses={
            200: OrganizationSerializer,
            404: OpenApiResponse(description="Organization not found"),
        },
        tags=["Organizations"],
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update Organization",
        description="Updates organization settings (restricted to OWNER and ADMIN).",
        request=OrganizationUpdateSerializer,
        responses={200: OrganizationSerializer, 403: OpenApiResponse(description="Forbidden")},
        tags=["Organizations"],
    )
    def patch(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(
            OrganizationSerializer(updated, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Delete Organization",
        description="Deletes an organization and all associated data (restricted to OWNER).",
        responses={
            204: OpenApiResponse(description="Organization deleted"),
            403: OpenApiResponse(description="Forbidden"),
        },
        tags=["Organizations"],
    )
    def delete(self, request: Request, *args, **kwargs) -> Response:
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganizationMemberListCreateView(APIView):
    """
    List members of an organization or invite/add a new member.
    """

    permission_classes = (IsAuthenticated,)

    def get_organization(self, organization_id: str) -> Organization:
        return get_object_or_404(
            Organization.objects.filter(members__user=self.request.user),
            id=organization_id,
        )

    @extend_schema(
        summary="List Organization Members",
        description="Returns all members belonging to the specified organization.",
        responses={200: OrganizationMemberSerializer(many=True)},
        tags=["Organizations"],
    )
    def get(self, request: Request, id: str) -> Response:
        organization = self.get_organization(id)
        members = organization.members.select_related("user").order_by("-created_at")
        serializer = OrganizationMemberSerializer(members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add / Invite Member",
        description="Adds a user to the organization with a specified role (restricted to OWNER and ADMIN).",
        request=OrganizationMemberCreateSerializer,
        responses={
            201: OrganizationMemberSerializer,
            403: OpenApiResponse(description="Forbidden"),
        },
        tags=["Organizations"],
    )
    def post(self, request: Request, id: str) -> Response:
        organization = self.get_organization(id)
        if not organization.is_admin_or_owner(request.user):
            raise PermissionDenied(
                "Seuls les propriétaires et administrateurs peuvent ajouter des membres."
            )

        serializer = OrganizationMemberCreateSerializer(
            data=request.data, context={"organization": organization}
        )
        serializer.is_valid(raise_exception=True)
        member = serializer.save()
        return Response(
            OrganizationMemberSerializer(member).data,
            status=status.HTTP_201_CREATED,
        )


class OrganizationMemberDetailView(APIView):
    """
    Update member role or remove member from organization.
    """

    permission_classes = (IsAuthenticated,)

    def get_organization_and_member(
        self, organization_id: str, member_id: str
    ) -> tuple[Organization, OrganizationMember]:
        organization = get_object_or_404(
            Organization.objects.filter(members__user=self.request.user),
            id=organization_id,
        )
        member = get_object_or_404(
            organization.members.select_related("user"),
            id=member_id,
        )
        return organization, member

    @extend_schema(
        summary="Update Member Role",
        description="Modifies a member's role (restricted to OWNER and ADMIN).",
        request=OrganizationMemberUpdateSerializer,
        responses={
            200: OrganizationMemberSerializer,
            403: OpenApiResponse(description="Forbidden"),
        },
        tags=["Organizations"],
    )
    def patch(self, request: Request, id: str, member_id: str) -> Response:
        organization, member = self.get_organization_and_member(id, member_id)

        if not organization.is_admin_or_owner(request.user):
            raise PermissionDenied(
                "Seuls les propriétaires et administrateurs peuvent modifier les rôles."
            )

        # Cannot modify role of owner unless caller is owner
        if member.role == RoleChoices.OWNER and not organization.is_owner(request.user):
            raise PermissionDenied(
                "Seul le propriétaire peut modifier le rôle d'un autre propriétaire."
            )

        serializer = OrganizationMemberUpdateSerializer(member, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_member = serializer.save()
        return Response(
            OrganizationMemberSerializer(updated_member).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Remove Member",
        description="Removes a member from the organization (restricted to OWNER, ADMIN, or self-removal).",
        responses={
            204: OpenApiResponse(description="Member removed"),
            403: OpenApiResponse(description="Forbidden"),
        },
        tags=["Organizations"],
    )
    def delete(self, request: Request, id: str, member_id: str) -> Response:
        organization, member = self.get_organization_and_member(id, member_id)

        is_self = member.user == request.user
        is_admin_or_owner = organization.is_admin_or_owner(request.user)

        if not (is_self or is_admin_or_owner):
            raise PermissionDenied("Vous n'avez pas l'autorisation de retirer ce membre.")

        # Prevent removing the last owner
        if member.role == RoleChoices.OWNER:
            owner_count = organization.members.filter(role=RoleChoices.OWNER).count()
            if owner_count <= 1:
                raise ValidationError(
                    {"detail": "Impossible de retirer le seul propriétaire de l'organisation."}
                )

        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
