from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from apps.organizations.models import RoleChoices


class IsCourseOrganizationMember(BasePermission):
    """Grants read/access permissions to users belonging to the course's organization."""

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", None)
        if not organization and hasattr(obj, "course"):
            organization = getattr(obj.course, "organization", None)

        if not organization:
            return False

        return organization.is_member(request.user)


class CanManageCourse(BasePermission):
    """Allows read access to all organization members (teachers, students, admins).

    Grants write/edit/delete and AI generation access strictly to:
    - Organization OWNER
    - Organization ADMIN
    - Organization TEACHER
    - Course creator (created_by)
    """

    def has_permission(self, request: Request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request: Request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        organization = getattr(obj, "organization", None)
        course_creator = getattr(obj, "created_by", None)

        if not organization and hasattr(obj, "course"):
            organization = getattr(obj.course, "organization", None)
            course_creator = getattr(obj.course, "created_by", None)

        if not organization or not organization.is_member(request.user):
            return False

        # Read-only methods allowed to all members (including students)
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        # Check write permissions (TEACHER, ADMIN, OWNER or course creator)
        user_role = organization.get_user_role(request.user)
        if user_role in (RoleChoices.OWNER, RoleChoices.ADMIN, RoleChoices.TEACHER):
            return True

        if course_creator == request.user:
            return True

        return False
