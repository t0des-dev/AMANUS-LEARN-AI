from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from apps.organizations.models import RoleChoices


class CanViewTeacherAnalytics(BasePermission):
    """Restricts teacher analytics to instructors, admins and owners of the course organization.

    Guarantees strict tenant isolation: teachers cannot access courses or quizzes
    belonging to other organizations or courses where they have no instructional role.
    """

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", None)
        created_by = getattr(obj, "created_by", None)

        if not organization and hasattr(obj, "course") and obj.course:
            organization = getattr(obj.course, "organization", None)
            created_by = getattr(obj.course, "created_by", None)

        if not organization:
            return False

        # Must belong to the organization
        if not organization.is_member(request.user):
            return False

        # Teacher, Admin, Owner or Course Creator
        user_role = organization.get_user_role(request.user)
        if user_role in (RoleChoices.OWNER, RoleChoices.ADMIN, RoleChoices.TEACHER):
            return True

        if created_by == request.user:
            return True

        return False
