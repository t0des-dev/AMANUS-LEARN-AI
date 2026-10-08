from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from apps.organizations.models import RoleChoices


class IsQuizOrganizationMember(BasePermission):
    """Allows access only to authenticated members belonging to the quiz's organization."""

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", None)
        if not organization and hasattr(obj, "quiz"):
            organization = getattr(obj.quiz, "organization", None)

        if not organization:
            return False

        return organization.is_member(request.user)


class CanManageQuiz(BasePermission):
    """Allows read access and attempt execution to all organization members.

    Restricts creation, editing, deletion, and AI generation to:
    - Organization OWNER
    - Organization ADMIN
    - Organization TEACHER
    - Quiz creator (created_by)
    """

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", None)
        creator = getattr(obj, "created_by", None)

        if not organization and hasattr(obj, "quiz"):
            organization = getattr(obj.quiz, "organization", None)
            creator = getattr(obj.quiz, "created_by", None)

        if not organization or not organization.is_member(request.user):
            return False

        # Read-only methods allowed to all members
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        # Check write permissions
        user_role = organization.get_user_role(request.user)
        if user_role in (RoleChoices.OWNER, RoleChoices.ADMIN, RoleChoices.TEACHER):
            return True

        if creator == request.user:
            return True

        return False
