from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from apps.organizations.models import RoleChoices


class IsAudioOrganizationMember(BasePermission):
    """Allows read access to members belonging to the course's organization."""

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        course = getattr(obj, "course", None)
        if not course:
            return False

        organization = course.organization
        return organization.is_member(request.user)


class CanManageAudio(BasePermission):
    """Allows managing (creating, regenerating, deleting) audio content:

    Granted to:
    - Organization OWNER
    - Organization ADMIN
    - Organization TEACHER
    - Course creator
    """

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        course = getattr(obj, "course", None)
        if not course:
            return False

        organization = course.organization
        if not organization.is_member(request.user):
            return False

        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        user_role = organization.get_user_role(request.user)
        if user_role in (RoleChoices.OWNER, RoleChoices.ADMIN, RoleChoices.TEACHER):
            return True

        if course.created_by == request.user:
            return True

        return False
