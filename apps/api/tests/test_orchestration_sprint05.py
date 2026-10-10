import uuid
from unittest.mock import MagicMock, patch

import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from apps.ai.models import GenerationStatus
from apps.ai.services.generation_service import GenerationService
from apps.ai.services.orchestration.cache_service import GenerationCacheService
from apps.ai.services.orchestration.cost_estimator import CostEstimator
from apps.ai.services.orchestration.lifecycle import (
    InvalidLifecycleTransitionError,
    TaskLifecycleStatus,
    map_celery_status_to_lifecycle,
    validate_status_transition,
)
from apps.ai.services.orchestration.lock_manager import (
    ConcurrentGenerationConflictError,
    GenerationLock,
    IdempotencyManager,
    generation_lock,
)
from apps.ai.services.orchestration.task_tracker import TaskTracker
from apps.ai.services.providers.mock_provider import MockAIProvider
from apps.courses.models import Course
from apps.slides.models import Presentation, PresentationStatus


@pytest.fixture(autouse=True)
def clear_django_cache():
    cache.clear()
    yield
    cache.clear()


# =========================================================================
# 1. Lifecycle Transitions Tests
# =========================================================================


class TestTaskLifecycle:
    def test_valid_lifecycle_transitions(self):
        # PENDING -> QUEUED -> RUNNING -> SUCCEEDED
        assert (
            validate_status_transition(TaskLifecycleStatus.PENDING, TaskLifecycleStatus.QUEUED)
            == TaskLifecycleStatus.QUEUED
        )
        assert (
            validate_status_transition(TaskLifecycleStatus.QUEUED, TaskLifecycleStatus.RUNNING)
            == TaskLifecycleStatus.RUNNING
        )
        assert (
            validate_status_transition(TaskLifecycleStatus.RUNNING, TaskLifecycleStatus.SUCCEEDED)
            == TaskLifecycleStatus.SUCCEEDED
        )

        # RUNNING -> RETRYING -> RUNNING -> FAILED
        assert (
            validate_status_transition(TaskLifecycleStatus.RUNNING, TaskLifecycleStatus.RETRYING)
            == TaskLifecycleStatus.RETRYING
        )
        assert (
            validate_status_transition(TaskLifecycleStatus.RETRYING, TaskLifecycleStatus.RUNNING)
            == TaskLifecycleStatus.RUNNING
        )
        assert (
            validate_status_transition(TaskLifecycleStatus.RUNNING, TaskLifecycleStatus.FAILED)
            == TaskLifecycleStatus.FAILED
        )

        # PENDING -> CANCELLED
        assert (
            validate_status_transition(TaskLifecycleStatus.PENDING, TaskLifecycleStatus.CANCELLED)
            == TaskLifecycleStatus.CANCELLED
        )

    def test_invalid_lifecycle_transitions_raise_error(self):
        with pytest.raises(InvalidLifecycleTransitionError) as exc:
            validate_status_transition(TaskLifecycleStatus.SUCCEEDED, TaskLifecycleStatus.RUNNING)
        assert "illégale" in str(exc.value)

        with pytest.raises(InvalidLifecycleTransitionError):
            validate_status_transition(TaskLifecycleStatus.FAILED, TaskLifecycleStatus.PENDING)

        with pytest.raises(InvalidLifecycleTransitionError):
            validate_status_transition(TaskLifecycleStatus.CANCELLED, TaskLifecycleStatus.RUNNING)

    def test_celery_status_mapping(self):
        assert map_celery_status_to_lifecycle("PENDING") == TaskLifecycleStatus.QUEUED
        assert map_celery_status_to_lifecycle("RECEIVED") == TaskLifecycleStatus.QUEUED
        assert map_celery_status_to_lifecycle("STARTED") == TaskLifecycleStatus.RUNNING
        assert map_celery_status_to_lifecycle("SUCCESS") == TaskLifecycleStatus.SUCCEEDED
        assert map_celery_status_to_lifecycle("FAILURE") == TaskLifecycleStatus.FAILED
        assert map_celery_status_to_lifecycle("RETRY") == TaskLifecycleStatus.RETRYING
        assert map_celery_status_to_lifecycle("REVOKED") == TaskLifecycleStatus.CANCELLED


# =========================================================================
# 2. Concurrency Lock & Idempotency Tests
# =========================================================================


class TestLockAndIdempotency:
    def test_generation_lock_acquire_and_release(self):
        resource_id = f"res-{uuid.uuid4()}"

        # First acquisition must succeed
        assert (
            GenerationLock.acquire(resource_type="course", resource_id=resource_id, timeout=30)
            is True
        )
        assert GenerationLock.is_locked(resource_type="course", resource_id=resource_id) is True

        # Second acquisition on same resource must fail
        with pytest.raises(ConcurrentGenerationConflictError) as exc:
            GenerationLock.acquire(resource_type="course", resource_id=resource_id, timeout=30)
        assert "en cours d'exécution" in str(exc.value)

        # Release lock
        GenerationLock.release(resource_type="course", resource_id=resource_id)
        assert GenerationLock.is_locked(resource_type="course", resource_id=resource_id) is False

        # Now acquisition succeeds again
        assert (
            GenerationLock.acquire(resource_type="course", resource_id=resource_id, timeout=30)
            is True
        )
        GenerationLock.release(resource_type="course", resource_id=resource_id)

    def test_generation_lock_context_manager_releases_on_exception(self):
        resource_id = f"res-{uuid.uuid4()}"

        with pytest.raises(RuntimeError):
            with generation_lock("quiz", resource_id, timeout=10):
                assert GenerationLock.is_locked("quiz", resource_id) is True
                raise RuntimeError("Worker crash simulation")

        # After exception, lock must be released
        assert GenerationLock.is_locked("quiz", resource_id) is False

    def test_idempotency_manager(self):
        idem_key = f"key-{uuid.uuid4()}"
        payload = {"course_id": str(uuid.uuid4()), "status": "completed"}

        assert IdempotencyManager.get_existing_result(idem_key) is None

        IdempotencyManager.record_result(idem_key, payload, ttl=60)

        assert IdempotencyManager.get_existing_result(idem_key) == payload


# =========================================================================
# 3. Generation Cache & Tenant Isolation Tests
# =========================================================================


@pytest.mark.django_db
class TestGenerationCache:
    def test_deterministic_fingerprint(self):
        fp1 = GenerationCacheService.compute_fingerprint(
            organization_id="org-1",
            resource_type="summary",
            content="Document text contents",
            prompt_version="v1.0",
            model="mock-model",
            language="fr",
            extra_params={"level": "intermédiaire"},
        )
        fp2 = GenerationCacheService.compute_fingerprint(
            organization_id="org-1",
            resource_type="summary",
            content="Document text contents",
            prompt_version="v1.0",
            model="mock-model",
            language="fr",
            extra_params={"level": "intermédiaire"},
        )
        assert fp1 == fp2

    def test_strict_tenant_isolation_in_cache(self):
        # Two different orgs with identical inputs must have different fingerprints and keys
        fp_org1 = GenerationCacheService.compute_fingerprint(
            organization_id="org-1",
            resource_type="summary",
            content="Shared syllabus content",
            prompt_version="v1.0",
            model="mock-model",
        )
        fp_org2 = GenerationCacheService.compute_fingerprint(
            organization_id="org-2",
            resource_type="summary",
            content="Shared syllabus content",
            prompt_version="v1.0",
            model="mock-model",
        )
        assert fp_org1 != fp_org2

        # Cache data for org-1
        GenerationCacheService.set_cached("org-1", fp_org1, {"summary": "Org 1 private analysis"})

        # Org-2 must get cache miss
        assert GenerationCacheService.get_cached("org-2", fp_org2) is None
        assert GenerationCacheService.get_cached("org-1", fp_org1) == {
            "summary": "Org 1 private analysis"
        }

    def test_content_modification_invalidates_fingerprint(self):
        fp_original = GenerationCacheService.compute_fingerprint(
            organization_id="org-1",
            resource_type="lesson",
            content="Version 1 of text",
            prompt_version="v1.0",
            model="mock-model",
        )
        fp_modified = GenerationCacheService.compute_fingerprint(
            organization_id="org-1",
            resource_type="lesson",
            content="Version 2 of text (updated)",
            prompt_version="v1.0",
            model="mock-model",
        )
        assert fp_original != fp_modified

    def test_explicit_invalidation(self):
        fp = GenerationCacheService.compute_fingerprint(
            organization_id="org-1",
            resource_type="summary",
            content="Cache invalidation test",
            prompt_version="v1.0",
            model="mock-model",
        )
        GenerationCacheService.set_cached("org-1", fp, {"result": "ok"})
        assert GenerationCacheService.get_cached("org-1", fp) is not None

        GenerationCacheService.invalidate("org-1", fp)
        assert GenerationCacheService.get_cached("org-1", fp) is None

    def test_generation_service_with_cache_opt_in(self, analyzed_document, tenant_setup):
        mock_provider = MockAIProvider()
        service = GenerationService(provider=mock_provider)
        user = tenant_setup["teacher"]

        # First call with use_cache=True generates and caches
        rec1 = service.generate_summary(
            document=analyzed_document,
            user=user,
            use_cache=True,
        )
        assert rec1.status == GenerationStatus.SUCCESS
        assert rec1.input_tokens > 0

        # Second call with use_cache=True retrieves from cache without token cost
        rec2 = service.generate_summary(
            document=analyzed_document,
            user=user,
            use_cache=True,
        )
        assert rec2.status == GenerationStatus.SUCCESS
        assert "cached" in rec2.provider
        assert rec2.input_tokens == 0
        assert rec2.output_tokens == 0


# =========================================================================
# 4. Cost Estimator & Observability Tests
# =========================================================================


class TestCostEstimator:
    def test_openai_token_cost_estimation(self):
        cost = CostEstimator.estimate_llm_cost(
            model="gpt-4o",
            input_tokens=1000,
            output_tokens=500,
        )
        # gpt-4o: (1000 / 1e6)*2.50 + (500 / 1e6)*10.00 = 0.0025 + 0.0050 = 0.0075
        assert cost == pytest.approx(0.0075, rel=1e-3)

    def test_anthropic_cost_estimation(self):
        cost = CostEstimator.estimate_llm_cost(
            model="claude-3-5-sonnet",
            input_tokens=2000,
            output_tokens=1000,
        )
        # 2000 / 1e6 * 3.00 + 1000 / 1e6 * 15.00 = 0.006 + 0.015 = 0.021
        assert cost == pytest.approx(0.021, rel=1e-3)

    def test_gemini_cost_estimation(self):
        cost = CostEstimator.estimate_llm_cost(
            model="gemini-1.5-flash",
            input_tokens=10000,
            output_tokens=2000,
        )
        # 10000 / 1e6 * 0.075 + 2000 / 1e6 * 0.30 = 0.00075 + 0.0006 = 0.00135
        assert cost == pytest.approx(0.00135, rel=1e-3)

    def test_audio_tts_cost_estimation(self):
        # ElevenLabs: 10,000 chars: (10000 / 1000) * 0.150 = $1.50
        cost_eleven = CostEstimator.estimate_tts_cost(
            voice_provider="elevenlabs",
            character_count=10000,
        )
        assert cost_eleven == pytest.approx(1.50, rel=1e-3)

        # OpenAI TTS: 5,000 chars: (5000 / 1000) * 0.015 = $0.075
        cost_openai = CostEstimator.estimate_tts_cost(
            voice_provider="openai",
            character_count=5000,
        )
        assert cost_openai == pytest.approx(0.075, rel=1e-3)

    def test_mock_provider_is_free(self):
        cost = CostEstimator.estimate_llm_cost(
            model="mock",
            input_tokens=5000,
            output_tokens=5000,
        )
        assert cost == 0.0

    def test_observability_summary_build(self):
        summary = CostEstimator.build_observability_summary(
            provider="openai",
            model="gpt-4o",
            duration_seconds=1.45,
            input_tokens=1000,
            output_tokens=500,
            attempts=1,
        )
        assert summary["provider"] == "openai"
        assert summary["model"] == "gpt-4o"
        assert summary["duration_seconds"] == 1.45
        assert summary["total_tokens"] == 1500
        assert summary["estimated_cost_usd"] == pytest.approx(0.0075, rel=1e-3)
        assert summary["is_cost_estimated"] is True


# =========================================================================
# 5. Task Tracker & API Endpoints Tests
# =========================================================================


@pytest.mark.django_db
class TestTaskTrackerAndAPI:
    def test_task_status_endpoint_returns_celery_status(self, tenant_setup):
        client = APIClient()
        teacher = tenant_setup["teacher"]
        client.force_authenticate(user=teacher)

        task_id = str(uuid.uuid4())

        # Register task ownership for teacher's organization
        TaskTracker.register_task_metadata(
            task_id=task_id,
            organization_id=str(tenant_setup["org_a"].id),
            task_name="generate_course_task",
            resource_type="course",
            resource_id="course-123",
        )

        with patch("apps.ai.services.orchestration.task_tracker.AsyncResult") as mock_async_res:
            mock_instance = MagicMock()
            mock_instance.state = "SUCCESS"
            mock_instance.status = "SUCCESS"
            mock_instance.ready.return_value = True
            mock_instance.successful.return_value = True
            mock_instance.result = {"course_id": "course-123"}
            mock_instance.date_done = None
            mock_async_res.return_value = mock_instance

            # Both URLs must be reachable
            response = client.get(f"/api/v1/tasks/{task_id}/")
            assert response.status_code == status.HTTP_200_OK
            assert response.data["task_id"] == task_id
            assert response.data["status"] == TaskLifecycleStatus.SUCCEEDED
            assert response.data["task_name"] == "generate_course_task"

            response_rag = client.get(f"/api/v1/ai/tasks/{task_id}/")
            assert response_rag.status_code == status.HTTP_200_OK
            assert response_rag.data["task_id"] == task_id

    def test_cross_tenant_task_access_forbidden(self, tenant_setup):
        client = APIClient()
        outsider = tenant_setup["outsider"]  # Member of org_b
        client.force_authenticate(user=outsider)

        task_id = str(uuid.uuid4())
        org_a_id = str(tenant_setup["org_a"].id)

        # Register task under Org A
        TaskTracker.register_task_metadata(
            task_id=task_id,
            organization_id=org_a_id,
            task_name="generate_course_task",
        )

        response = client.get(f"/api/v1/tasks/{task_id}/")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "task_access_denied"

    def test_unauthenticated_task_access_rejected(self):
        client = APIClient()
        task_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/tasks/{task_id}/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# =========================================================================
# 6. Generator Concurrency & 409 Conflict Integration Tests
# =========================================================================


@pytest.mark.django_db
class TestGeneratorConcurrencyConflict:
    def test_course_generation_returns_409_when_lock_active(self, tenant_setup, analyzed_document):
        client = APIClient()
        teacher = tenant_setup["teacher"]
        client.force_authenticate(user=teacher)

        course = Course.objects.create(
            title="Course Concurrency Test",
            organization=tenant_setup["org_a"],
            created_by=teacher,
        )

        # Simulate concurrent active generation lock
        GenerationLock.acquire(resource_type="course", resource_id=str(course.id))

        try:
            url = f"/api/v1/courses/{course.id}/generate/"
            response = client.post(
                url,
                {"document_id": str(analyzed_document.id)},
                format="json",
            )
            assert response.status_code == status.HTTP_409_CONFLICT
            assert response.data["code"] == "generation_in_progress"
            assert "déjà en cours" in response.data["detail"]
        finally:
            GenerationLock.release(resource_type="course", resource_id=str(course.id))

    def test_presentation_export_returns_409_when_already_exporting(self, tenant_setup):
        client = APIClient()
        teacher = tenant_setup["teacher"]
        client.force_authenticate(user=teacher)

        course = Course.objects.create(
            title="Slide Course",
            organization=tenant_setup["org_a"],
            created_by=teacher,
        )

        presentation = Presentation.objects.create(
            course=course,
            title="Slide Presentation Exporting",
            status=PresentationStatus.EXPORTING,
        )

        url = f"/api/v1/slides/presentations/{presentation.id}/export/"
        response = client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.data["code"] == "export_already_in_progress"
