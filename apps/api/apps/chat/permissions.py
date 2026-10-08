from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class IsSessionOwnerOrOrgAdmin(BasePermission):
    """Grants access to the chat session owner or organization administrators."""

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", None)
        if not organization or not organization.is_member(request.user):
            return False

        # Owner of the session
        if getattr(obj, "user", None) == request.user:
            return True

        # Organization Admin or Owner
        if organization.is_admin_or_owner(request.user):
            return True

        return False
