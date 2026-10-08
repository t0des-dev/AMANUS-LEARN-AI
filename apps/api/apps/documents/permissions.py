from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from apps.organizations.models import RoleChoices


class IsDocumentOrganizationMember(BasePermission):
    """Allows access only to authenticated members belonging to the document's organization."""

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", None)
        if not organization:
            return False

        return organization.is_member(request.user)


class CanManageDocument(BasePermission):
    """Allows read access to all organization members;

    write, delete, or pipeline execution access is granted to:
    - Organization OWNER
    - Organization ADMIN
    - Document creator (owner)
    - Organization TEACHER
    """

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", None)
        if not organization:
            return False

        # Must be an organization member in all cases
        if not organization.is_member(request.user):
            return False

        # Read-only methods (GET, HEAD, OPTIONS) allowed for all members
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        # Check write / delete permissions
        user_role = organization.get_user_role(request.user)
        if user_role in (RoleChoices.OWNER, RoleChoices.ADMIN, RoleChoices.TEACHER):
            return True

        # Creator of document
        if obj.owner == request.user:
            return True

        return False
