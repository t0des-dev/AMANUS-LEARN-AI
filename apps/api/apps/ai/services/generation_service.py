import logging
from typing import Any

from django.contrib.auth import get_user_model

from apps.ai.models import AIGeneration, GenerationStatus, GenerationType
from apps.documents.models import Document

from .generators import (
    BaseGenerator,
    InsufficientContextError,
    KeyPointGenerator,
    LessonGenerator,
    ObjectiveGenerator,
    RevisionSheetGenerator,
    SummaryGenerator,
)
from .providers import AIProvider, get_ai_provider

User = get_user_model()
logger = logging.getLogger(__name__)


class GenerationService:
    """Coordinates specialized pedagogical generators and maintains an immutable audit trail in AIGeneration."""

    GENERATOR_MAP: dict[str, type[BaseGenerator]] = {
        GenerationType.SUMMARY: SummaryGenerator,
        GenerationType.KEY_POINTS: KeyPointGenerator,
        GenerationType.OBJECTIVES: ObjectiveGenerator,
        GenerationType.LESSON: LessonGenerator,
        GenerationType.REVISION_SHEET: RevisionSheetGenerator,
    }

    def __init__(self, provider: AIProvider | None = None):
        self.default_provider = provider

    def get_generator(self, generation_type: str) -> BaseGenerator:
        """Instantiates the specialized generator for the requested type."""
        generator_cls = self.GENERATOR_MAP.get(generation_type)
        if not generator_cls:
            raise ValueError(f"Type de génération non supporté : {generation_type}")
        return generator_cls()

    def generate(
        self,
        document: Document,
        generation_type: str,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
        language: str | None = None,
        level: str | None = None,
        use_cache: bool = False,
        **kwargs: Any,
    ) -> AIGeneration:
        """Executes generation pipeline with full audit persistence in AIGeneration."""
        provider = self.default_provider or get_ai_provider(provider_name)
        active_model = model or getattr(provider, "default_model", "default")
        generator = self.get_generator(generation_type)
        prompt_version = getattr(generator, "prompt_version", "v1.0")

        # Check tenant-isolated cache if opted in
        cache_fingerprint = None
        org_id = str(document.organization_id)
        if use_cache:
            from .orchestration.cache_service import GenerationCacheService

            doc_updated = getattr(document, "updated_at", None)
            content_key = (
                f"{document.id}:{doc_updated.isoformat() if doc_updated else ''}:{focus or ''}"
            )
            cache_fingerprint = GenerationCacheService.compute_fingerprint(
                organization_id=org_id,
                resource_type=generation_type,
                content=content_key,
                prompt_version=prompt_version,
                model=active_model,
                language=language or "fr",
                extra_params={"level": level, "top_k": top_k},
            )
            cached_data = GenerationCacheService.get_cached(org_id, cache_fingerprint)
            if cached_data:
                logger.info(
                    "Returning cached generation for doc %s type %s", document.id, generation_type
                )
                return AIGeneration.objects.create(
                    organization=document.organization,
                    user=user if getattr(user, "is_authenticated", False) else None,
                    document=document,
                    type=generation_type,
                    provider=getattr(provider, "name", "mock") + "-cached",
                    model=active_model,
                    prompt_version=prompt_version,
                    status=GenerationStatus.SUCCESS,
                    result=cached_data.get("result", {}),
                    input_tokens=0,
                    output_tokens=0,
                    error="",
                )

        # 1. Initialize audit record in DB with PENDING status
        generation_record = AIGeneration.objects.create(
            organization=document.organization,
            user=user if getattr(user, "is_authenticated", False) else None,
            document=document,
            type=generation_type,
            provider=getattr(provider, "name", "mock"),
            model=active_model,
            prompt_version="pending",
            status=GenerationStatus.PENDING,
            result={},
            error="",
        )

        try:
            # 2. Run generation with RAG retrieval and strict safeguards
            structured_result, ai_response, prompt_version = generator.generate(
                document=document,
                provider=provider,
                model=model,
                focus=focus,
                top_k=top_k,
                language=language,
                level=level,
                **kwargs,
            )

            # 3. Persist success audit
            generation_record.status = GenerationStatus.SUCCESS
            generation_record.result = structured_result
            generation_record.input_tokens = ai_response.input_tokens
            generation_record.output_tokens = ai_response.output_tokens
            generation_record.model = ai_response.model
            generation_record.prompt_version = prompt_version
            generation_record.save(
                update_fields=[
                    "status",
                    "result",
                    "input_tokens",
                    "output_tokens",
                    "model",
                    "prompt_version",
                ]
            )

            if use_cache and cache_fingerprint:
                from .orchestration.cache_service import GenerationCacheService

                GenerationCacheService.set_cached(
                    organization_id=org_id,
                    fingerprint=cache_fingerprint,
                    result_data={"result": structured_result},
                )

            logger.info(
                "AIGeneration %s [%s] completed successfully for doc %s (in: %s, out: %s tokens)",
                generation_record.id,
                generation_type,
                document.id,
                ai_response.input_tokens,
                ai_response.output_tokens,
            )
            return generation_record

        except InsufficientContextError as exc:
            logger.warning(
                "AIGeneration %s failed due to insufficient context: %s",
                generation_record.id,
                exc,
            )
            generation_record.status = GenerationStatus.FAILED
            generation_record.error = str(exc)
            generation_record.save(update_fields=["status", "error"])
            raise

        except Exception as exc:
            logger.exception(
                "AIGeneration %s encountered an unexpected error: %s",
                generation_record.id,
                exc,
            )
            generation_record.status = GenerationStatus.FAILED
            generation_record.error = str(exc)
            generation_record.save(update_fields=["status", "error"])
            raise

    def generate_summary(
        self,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
        language: str | None = None,
        level: str | None = None,
        use_cache: bool = False,
        summary_level: str = "synthetic",
    ) -> AIGeneration:
        return self.generate(
            document=document,
            generation_type=GenerationType.SUMMARY,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
            language=language,
            level=level,
            use_cache=use_cache,
            summary_level=summary_level,
        )

    def generate_key_points(
        self,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
        language: str | None = None,
        level: str | None = None,
        use_cache: bool = False,
    ) -> AIGeneration:
        return self.generate(
            document=document,
            generation_type=GenerationType.KEY_POINTS,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
            language=language,
            level=level,
            use_cache=use_cache,
        )

    def generate_objectives(
        self,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
        language: str | None = None,
        level: str | None = None,
        use_cache: bool = False,
    ) -> AIGeneration:
        return self.generate(
            document=document,
            generation_type=GenerationType.OBJECTIVES,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
            language=language,
            level=level,
            use_cache=use_cache,
        )

    def generate_lesson(
        self,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
        language: str | None = None,
        level: str | None = None,
        use_cache: bool = False,
    ) -> AIGeneration:
        return self.generate(
            document=document,
            generation_type=GenerationType.LESSON,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
            language=language,
            level=level,
            use_cache=use_cache,
        )

    def generate_revision_sheet(
        self,
        document: Document,
        user: Any | None = None,
        provider_name: str | None = None,
        model: str | None = None,
        focus: str | None = None,
        top_k: int = 5,
        language: str | None = None,
        level: str | None = None,
        use_cache: bool = False,
    ) -> AIGeneration:
        return self.generate(
            document=document,
            generation_type=GenerationType.REVISION_SHEET,
            user=user,
            provider_name=provider_name,
            model=model,
            focus=focus,
            top_k=top_k,
            language=language,
            level=level,
            use_cache=use_cache,
        )
