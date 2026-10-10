import logging

from django.db import models

logger = logging.getLogger(__name__)


class TaskLifecycleStatus(models.TextChoices):
    """Unified lifecycle statuses for all AI generation and background tasks."""

    PENDING = "PENDING", "En attente"
    QUEUED = "QUEUED", "En file d'attente"
    RUNNING = "RUNNING", "En cours d'exécution"
    SUCCEEDED = "SUCCEEDED", "Succès"
    FAILED = "FAILED", "Échec"
    CANCELLED = "CANCELLED", "Annulé"
    RETRYING = "RETRYING", "Nouvelle tentative"


class InvalidStateTransitionError(Exception):
    """Raised when an illegal lifecycle state transition is attempted."""

    pass


InvalidLifecycleTransitionError = InvalidStateTransitionError


# Legal state machine transitions
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    TaskLifecycleStatus.PENDING: {
        TaskLifecycleStatus.QUEUED,
        TaskLifecycleStatus.RUNNING,
        TaskLifecycleStatus.CANCELLED,
        TaskLifecycleStatus.FAILED,
    },
    TaskLifecycleStatus.QUEUED: {
        TaskLifecycleStatus.RUNNING,
        TaskLifecycleStatus.CANCELLED,
        TaskLifecycleStatus.FAILED,
    },
    TaskLifecycleStatus.RUNNING: {
        TaskLifecycleStatus.SUCCEEDED,
        TaskLifecycleStatus.FAILED,
        TaskLifecycleStatus.RETRYING,
        TaskLifecycleStatus.CANCELLED,
    },
    TaskLifecycleStatus.RETRYING: {
        TaskLifecycleStatus.RUNNING,
        TaskLifecycleStatus.FAILED,
        TaskLifecycleStatus.CANCELLED,
    },
    # Terminal states
    TaskLifecycleStatus.SUCCEEDED: set(),
    TaskLifecycleStatus.CANCELLED: set(),
    # FAILED can only transition to QUEUED or RUNNING upon explicit manual restart/retry
    TaskLifecycleStatus.FAILED: {
        TaskLifecycleStatus.QUEUED,
        TaskLifecycleStatus.RUNNING,
    },
}


def validate_status_transition(current_status: str, next_status: str) -> None:
    """Validates that transition from current_status to next_status is legal.

    Raises:
        InvalidStateTransitionError: if the transition violates the state machine.
    """
    curr = str(current_status).upper()
    target = str(next_status).upper()

    if curr == target:
        # Idempotent re-affirmation of current status
        return target

    allowed = ALLOWED_TRANSITIONS.get(curr)
    if allowed is None:
        raise InvalidStateTransitionError(f"Statut actuel inconnu : {current_status}")

    if target not in allowed:
        raise InvalidStateTransitionError(
            f"Transition d'état illégale : impossible de passer de {curr} à {target}."
        )

    return target


def map_celery_status_to_lifecycle(celery_state: str) -> str:
    """Normalizes Celery internal task state to unified TaskLifecycleStatus."""
    state = str(celery_state).upper()
    mapping = {
        "PENDING": TaskLifecycleStatus.QUEUED,
        "RECEIVED": TaskLifecycleStatus.QUEUED,
        "STARTED": TaskLifecycleStatus.RUNNING,
        "RETRY": TaskLifecycleStatus.RETRYING,
        "SUCCESS": TaskLifecycleStatus.SUCCEEDED,
        "FAILURE": TaskLifecycleStatus.FAILED,
        "REVOKED": TaskLifecycleStatus.CANCELLED,
    }
    return mapping.get(state, TaskLifecycleStatus.RUNNING)
