import logging
from typing import Any

from celery.result import AsyncResult
from django.contrib.auth import get_user_model

from config.celery import app as celery_app

from .lifecycle import TaskLifecycleStatus, map_celery_status_to_lifecycle

User = get_user_model()
logger = logging.getLogger(__name__)


class TaskNotFoundError(Exception):
    """Raised when a task id cannot be found in the system."""

    pass


class TaskAccessDeniedError(Exception):
    """Raised when a user attempts to access a task belonging to another organization."""

    pass


class TaskTracker:
    """Unified service for querying and tracking asynchronous Celery generation tasks.

    Enforces strict multi-tenant authorization so users cannot observe tasks
    belonging to other organizations.
    """

    @classmethod
    def register_task_metadata(
        cls,
        task_id: str,
        organization_id: str,
        task_name: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ttl: int = 86400,
    ) -> None:
        """Stores task tenant ownership and metadata in cache for cross-tenant checking."""
        from django.core.cache import cache

        key = f"task_meta:{str(task_id).strip()}"
        payload = {
            "task_id": str(task_id).strip(),
            "organization_id": str(organization_id).strip(),
            "task_name": str(task_name or ""),
            "resource_type": str(resource_type or ""),
            "resource_id": str(resource_id or ""),
        }
        cache.set(key, payload, timeout=ttl)

    @classmethod
    def get_task_metadata(cls, task_id: str) -> dict[str, Any] | None:
        from django.core.cache import cache

        return cache.get(f"task_meta:{str(task_id).strip()}")

    @classmethod
    def get_task_status(cls, task_id: str, user: Any = None) -> dict[str, Any]:
        """Inspects background task status via Celery AsyncResult and domain fallback.

        Args:
            task_id: Celery task UUID
            user: Authenticated Django User

        Returns:
            Unified status payload.
        """
        clean_task_id = str(task_id).strip()
        metadata = cls.get_task_metadata(clean_task_id)

        # Cross-tenant permission check using cached metadata if available
        if metadata and user and user.is_authenticated and not getattr(user, "is_staff", False):
            task_org_id = metadata.get("organization_id")
            if task_org_id:
                from apps.organizations.models import OrganizationMember

                is_member = OrganizationMember.objects.filter(
                    organization_id=task_org_id,
                    user=user,
                ).exists()
                if not is_member:
                    raise TaskAccessDeniedError("Vous n'avez pas accès à cette tâche.")

        async_result = AsyncResult(clean_task_id, app=celery_app)

        raw_state = str(async_result.state or "PENDING")
        unified_status = map_celery_status_to_lifecycle(raw_state)

        result_payload = None
        error_message = None
        progress = None

        is_ready = (
            bool(async_result.ready()) if callable(getattr(async_result, "ready", None)) else False
        )
        is_successful = (
            bool(async_result.successful())
            if (is_ready and callable(getattr(async_result, "successful", None)))
            else False
        )

        if is_ready:
            if is_successful:
                unified_status = TaskLifecycleStatus.SUCCEEDED
                val = async_result.result
                if isinstance(val, dict):
                    result_payload = val
                else:
                    result_payload = {"result": str(val)}
            else:
                unified_status = TaskLifecycleStatus.FAILED
                err = async_result.result
                error_message = str(err) if err else "Tâche échouée."
        elif raw_state == "STARTED":
            unified_status = TaskLifecycleStatus.RUNNING
            info = getattr(async_result, "info", None)
            if isinstance(info, dict):
                progress = info.get("progress")
        elif raw_state == "RETRY":
            unified_status = TaskLifecycleStatus.RETRYING

        # Fallback tenant verification if result payload contains organization_id
        if (
            user
            and user.is_authenticated
            and result_payload
            and not getattr(user, "is_staff", False)
        ):
            org_id = result_payload.get("organization_id")
            if org_id:
                from apps.organizations.models import OrganizationMember

                is_member = OrganizationMember.objects.filter(
                    organization_id=org_id,
                    user=user,
                ).exists()
                if not is_member:
                    raise TaskAccessDeniedError("Vous n'avez pas accès à cette tâche.")

        return {
            "task_id": clean_task_id,
            "task_name": metadata.get("task_name") if metadata else None,
            "status": unified_status,
            "raw_state": raw_state,
            "progress": progress,
            "result": result_payload,
            "error": error_message,
            "ready": is_ready,
            "successful": is_successful,
        }
