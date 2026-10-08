from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from .models import Organization


class IsOrganizationMember(BasePermission):
    """Allows access only to authenticated members of the organization."""

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj: Organization) -> bool:
        organization = obj if isinstance(obj, Organization) else getattr(obj, "organization", None)
        if not organization:
            return False
        return organization.is_member(request.user)


class IsOrganizationAdminOrOwner(BasePermission):
    """Allows write/admin access only to OWNER or ADMIN members of the organization."""

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj: Organization) -> bool:
        organization = obj if isinstance(obj, Organization) else getattr(obj, "organization", None)
        if not organization:
            return False
        return organization.is_admin_or_owner(request.user)


class IsOrganizationOwner(BasePermission):
    """Allows sensitive operations (e.g. deletion, transfer) only to the OWNER."""

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj: Organization) -> bool:
        organization = obj if isinstance(obj, Organization) else getattr(obj, "organization", None)
        if not organization:
            return False
        return organization.is_owner(request.user)
