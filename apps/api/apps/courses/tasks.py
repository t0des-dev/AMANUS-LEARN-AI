import logging
from typing import Any

from celery import shared_task
from django.contrib.auth import get_user_model

from apps.courses.models import Course
from apps.courses.services.builder import CourseBuilderService
from apps.documents.models import Document

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, queue="heavy", max_retries=2, default_retry_delay=15)
def generate_course_task(
    self,
    course_id: str,
    document_id: str | None = None,
    user_id: int | str | None = None,
    provider: str | None = None,
    provider_name: str | None = None,
    model: str | None = None,
    focus: str | None = None,
    top_k: int = 10,
    language: str | None = None,
    level: str | None = None,
    preserve_existing: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    """Celery background task for asynchronous, resilient course generation.

    Routed to the 'heavy' queue to prevent starving transactional API threads.
    """
    logger.info("[Celery] Starting asynchronous course generation for Course %s", course_id)
    active_provider = provider or provider_name
    try:
        course = Course.objects.select_related("organization").get(id=course_id)
        effective_doc_id = document_id or (str(course.document_id) if course.document_id else None)
        if not effective_doc_id:
            logger.error("[Celery] No source document for Course %s", course_id)
            return {"status": "ERROR", "error": "Aucun document associé au cours."}

        document = Document.objects.get(id=effective_doc_id, organization=course.organization)

        user = None
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                user = None

        builder = CourseBuilderService()
        updated_course = builder.generate_course_from_document(
            course=course,
            document=document,
            user=user,
            provider_name=active_provider,
            model=model,
            focus=focus,
            top_k=top_k,
            language=language,
            level=level,
            preserve_existing=preserve_existing,
        )

        logger.info(
            "[Celery] Course generation completed successfully for Course %s (%d sections)",
            course_id,
            updated_course.sections.count(),
        )
        return {
            "status": "SUCCESS",
            "course_id": str(updated_course.id),
            "title": updated_course.title,
            "sections_count": updated_course.sections.count(),
        }

    except Course.DoesNotExist:
        logger.error("[Celery] Course %s not found for generation task", course_id)
        return {"status": "ERROR", "error": f"Cours introuvable ({course_id})"}
    except Document.DoesNotExist:
        logger.error("[Celery] Document %s not found for Course %s", document_id, course_id)
        return {"status": "ERROR", "error": f"Document introuvable ({document_id})"}
    except Exception as exc:
        logger.error(
            "[Celery] Course generation failed for Course %s: %s", course_id, exc, exc_info=True
        )
        raise self.retry(exc=exc)
    finally:
        from apps.ai.services.orchestration import GenerationLock

        GenerationLock.release("course", str(course_id))
