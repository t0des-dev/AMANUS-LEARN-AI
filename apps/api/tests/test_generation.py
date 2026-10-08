import uuid

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.ai.models import AIGeneration, GenerationStatus, GenerationType
from apps.ai.services import (
    AIService,
    GenerationService,
    InsufficientContextError,
    KeyPointGenerator,
    LessonGenerator,
    MockAIProvider,
    ObjectiveGenerator,
    PromptService,
    SummaryGenerator,
    get_ai_provider,
)
from apps.documents.models import Document, DocumentStatus
from apps.ingestion.models import DocumentChunk, DocumentPage
from apps.organizations.models import Organization, OrganizationMember, RoleChoices


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def users_and_orgs(db):
    user_a = User.objects.create_user(
        email="alice@test.com",
        password="SecurePassword123!",
        first_name="Alice",
        last_name="OrgA",
    )
    user_b = User.objects.create_user(
        email="bob@test.com",
        password="SecurePassword123!",
        first_name="Bob",
        last_name="OrgB",
    )

    org_a = Organization.objects.create(name="Organization Alpha", slug="org-alpha")
    OrganizationMember.objects.create(organization=org_a, user=user_a, role=RoleChoices.OWNER)

    org_b = Organization.objects.create(name="Organization Beta", slug="org-beta")
    OrganizationMember.objects.create(organization=org_b, user=user_b, role=RoleChoices.OWNER)

    return {
        "user_a": user_a,
        "user_b": user_b,
        "org_a": org_a,
        "org_b": org_b,
    }


@pytest.fixture
def document_with_chunks(db, users_and_orgs):
    org = users_and_orgs["org_a"]
    user = users_and_orgs["user_a"]

    doc = Document.objects.create(
        organization=org,
        owner=user,
        title="Introduction au Deep Learning",
        file_name="deep_learning.pdf",
        file_type="pdf",
        file_size=1024,
        storage_key="test/deep_learning.pdf",
        status=DocumentStatus.READY,
    )

    page_1 = DocumentPage.objects.create(
        document=doc,
        page_number=1,
        text="Introduction aux réseaux de neurones artificiels et à la rétropropagation.",
    )

    DocumentChunk.objects.create(
        document=doc,
        page=page_1,
        chunk_index=0,
        content=(
            "Les réseaux de neurones artificiels sont des modèles computationnels inspirés "
            "du cerveau humain. Le mécanisme d'attention permet de focaliser les calculs sur les "
            "tokens les plus pertinents de la séquence."
        ),
        token_count=35,
        metadata={"chapter": "Chapitre 1", "section": "Fondements"},
        embedding=[0.05] * 128,
    )

    DocumentChunk.objects.create(
        document=doc,
        page=page_1,
        chunk_index=1,
        content=(
            "L'algorithme de rétropropagation du gradient ajuste les poids synaptiques pour "
            "minimiser la fonction de perte au moyen de l'optimiseur Adam ou SGD."
        ),
        token_count=30,
        metadata={"chapter": "Chapitre 1", "section": "Optimisation"},
        embedding=[0.08] * 128,
    )

    return doc


@pytest.fixture
def empty_document(db, users_and_orgs):
    org = users_and_orgs["org_a"]
    user = users_and_orgs["user_a"]

    return Document.objects.create(
        organization=org,
        owner=user,
        title="Document Vide Sans Chunks",
        file_name="empty.pdf",
        file_type="pdf",
        file_size=512,
        storage_key="test/empty.pdf",
        status=DocumentStatus.UPLOADED,
    )


# =========================================================================
# Unit Tests: Providers & PromptService
# =========================================================================


@pytest.mark.django_db
class TestAIProvidersAndPrompts:
    def test_mock_provider_json_generation(self):
        provider = MockAIProvider()
        resp = provider.generate(
            prompt="Créer un résumé",
            system_instruction="Règle",
            response_format="json",
        )
        assert resp.parsed_json is not None
        assert "overview" in resp.parsed_json
        assert resp.input_tokens > 0
        assert resp.output_tokens > 0
        assert resp.provider == "mock"

    def test_provider_factory_and_fallbacks(self):
        p_mock = get_ai_provider("mock")
        assert isinstance(p_mock, MockAIProvider)

        # Fallback to Mock if API keys missing
        p_openai = get_ai_provider("openai")
        assert p_openai is not None
        p_anthropic = get_ai_provider("anthropic")
        assert p_anthropic is not None
        p_gemini = get_ai_provider("gemini")
        assert p_gemini is not None
        p_local = get_ai_provider("local")
        assert p_local is not None

    def test_prompt_service_versions_and_rules(self):
        service = PromptService()
        assert service.VERSION == "v1.0"
        assert "RÈGLES ABSOLUES" in service.BASE_SYSTEM_INSTRUCTION
        assert "zéro hallucination" in service.BASE_SYSTEM_INSTRUCTION

        sys_p, user_p, ver = service.get_summary_prompt("Titre", "Contexte extrait")
        assert "Titre" in user_p
        assert "Contexte extrait" in user_p
        assert ver == "summary-v1.0"

        _, _, k_ver = service.get_key_points_prompt("Titre", "Contexte")
        assert k_ver == "key-points-v1.0"

        _, _, o_ver = service.get_objectives_prompt("Titre", "Contexte")
        assert o_ver == "objectives-v1.0"

        _, _, l_ver = service.get_lesson_prompt("Titre", "Contexte")
        assert l_ver == "lesson-v1.0"


# =========================================================================
# Unit Tests: Specialized Generators & Safeguards
# =========================================================================


@pytest.mark.django_db
class TestSpecializedGenerators:
    def test_summary_generator_safeguard_refuses_empty_document(self, empty_document):
        generator = SummaryGenerator()
        provider = MockAIProvider()

        with pytest.raises(InsufficientContextError) as exc_info:
            generator.generate(document=empty_document, provider=provider)

        assert "n'a pas encore été analysé" in str(exc_info.value)

    def test_summary_generator_success_with_citations(self, document_with_chunks):
        generator = SummaryGenerator()
        provider = MockAIProvider()

        result, ai_resp, prompt_ver = generator.generate(
            document=document_with_chunks,
            provider=provider,
        )

        assert prompt_ver.startswith("summary-")
        assert "citations" in result
        assert len(result["citations"]) > 0
        assert result["citations"][0]["document_title"] == document_with_chunks.title
        assert "overview" in result
        assert ai_resp.input_tokens > 0

    def test_key_points_generator_success(self, document_with_chunks):
        generator = KeyPointGenerator()
        provider = MockAIProvider()

        result, _, prompt_ver = generator.generate(
            document=document_with_chunks,
            provider=provider,
        )
        assert prompt_ver.startswith("key-points-")
        assert "key_points" in result
        assert len(result["key_points"]) > 0

    def test_objectives_generator_success(self, document_with_chunks):
        generator = ObjectiveGenerator()
        provider = MockAIProvider()

        result, _, prompt_ver = generator.generate(
            document=document_with_chunks,
            provider=provider,
        )
        assert prompt_ver.startswith("objectives-")
        assert "objectives" in result

    def test_lesson_generator_success(self, document_with_chunks):
        generator = LessonGenerator()
        provider = MockAIProvider()

        result, _, prompt_ver = generator.generate(
            document=document_with_chunks,
            provider=provider,
        )
        assert prompt_ver.startswith("lesson-")
        assert "sections" in result


# =========================================================================
# Integration Tests: GenerationService & AIService
# =========================================================================


@pytest.mark.django_db
class TestGenerationServiceAndAuditTrail:
    def test_generation_service_creates_immutable_audit(self, document_with_chunks, users_and_orgs):
        service = GenerationService(provider=MockAIProvider())
        user = users_and_orgs["user_a"]

        record = service.generate_summary(
            document=document_with_chunks,
            user=user,
        )

        assert isinstance(record, AIGeneration)
        assert record.status == GenerationStatus.SUCCESS
        assert record.type == GenerationType.SUMMARY
        assert record.document == document_with_chunks
        assert record.organization == document_with_chunks.organization
        assert record.user == user
        assert record.provider == "mock"
        assert record.input_tokens > 0
        assert record.output_tokens > 0
        assert "overview" in record.result

        # Verify DB row
        db_record = AIGeneration.objects.get(id=record.id)
        assert db_record.status == GenerationStatus.SUCCESS

    def test_generation_service_logs_failure_on_insufficient_context(
        self, empty_document, users_and_orgs
    ):
        service = GenerationService(provider=MockAIProvider())
        user = users_and_orgs["user_a"]

        with pytest.raises(InsufficientContextError):
            service.generate_lesson(document=empty_document, user=user)

        # Audit row should be stored with FAILED status
        failed_records = AIGeneration.objects.filter(
            document=empty_document, status=GenerationStatus.FAILED
        )
        assert failed_records.exists()
        failed_record = failed_records.first()
        assert failed_record.type == GenerationType.LESSON
        assert "n'a pas encore été analysé" in failed_record.error

    def test_ai_service_facade_dispatches_cleanly(self, document_with_chunks):
        ai_service = AIService()
        rec_summary = ai_service.generate_summary(document_with_chunks)
        assert rec_summary.type == GenerationType.SUMMARY
        assert rec_summary.status == GenerationStatus.SUCCESS

        rec_course = ai_service.generate_course(document_with_chunks)
        assert rec_course.type == GenerationType.LESSON
        assert rec_course.status == GenerationStatus.SUCCESS

        rec_obj = ai_service.generate_objectives(document_with_chunks)
        assert rec_obj.type == GenerationType.OBJECTIVES
        assert rec_obj.status == GenerationStatus.SUCCESS

        rec_kp = ai_service.generate_key_points(document_with_chunks)
        assert rec_kp.type == GenerationType.KEY_POINTS
        assert rec_kp.status == GenerationStatus.SUCCESS


# =========================================================================
# Integration Tests: REST API Endpoints
# =========================================================================


@pytest.mark.django_db
class TestGenerationAPIEndpoints:
    def test_generate_summary_endpoint_success(
        self, api_client, document_with_chunks, users_and_orgs
    ):
        user = users_and_orgs["user_a"]
        api_client.force_authenticate(user=user)

        url = f"/api/v1/documents/{document_with_chunks.id}/generate/summary/"
        payload = {"provider": "mock", "top_k": 3}

        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        data = response.data
        assert data["type"] == "SUMMARY"
        assert data["status"] == "SUCCESS"
        assert data["provider"] == "mock"
        assert data["input_tokens"] > 0
        assert data["output_tokens"] > 0
        assert "overview" in data["result"]
        assert "citations" in data["result"]

    def test_generate_course_endpoint_success(
        self, api_client, document_with_chunks, users_and_orgs
    ):
        user = users_and_orgs["user_a"]
        api_client.force_authenticate(user=user)

        url = f"/api/v1/documents/{document_with_chunks.id}/generate/course/"
        response = api_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        data = response.data
        assert data["type"] == "LESSON"
        assert data["status"] == "SUCCESS"
        assert "sections" in data["result"]

    def test_generate_objectives_endpoint_success(
        self, api_client, document_with_chunks, users_and_orgs
    ):
        user = users_and_orgs["user_a"]
        api_client.force_authenticate(user=user)

        url = f"/api/v1/documents/{document_with_chunks.id}/generate/objectives/"
        response = api_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        data = response.data
        assert data["type"] == "OBJECTIVES"
        assert "objectives" in data["result"]

    def test_generate_key_points_endpoint_success(
        self, api_client, document_with_chunks, users_and_orgs
    ):
        user = users_and_orgs["user_a"]
        api_client.force_authenticate(user=user)

        url = f"/api/v1/documents/{document_with_chunks.id}/generate/key-points/"
        response = api_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        data = response.data
        assert data["type"] == "KEY_POINTS"
        assert "key_points" in data["result"]

    def test_insufficient_context_returns_bad_request(
        self, api_client, empty_document, users_and_orgs
    ):
        user = users_and_orgs["user_a"]
        api_client.force_authenticate(user=user)

        url = f"/api/v1/documents/{empty_document.id}/generate/summary/"
        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["code"] == "insufficient_context"

    def test_cross_tenant_generation_forbidden(
        self, api_client, document_with_chunks, users_and_orgs
    ):
        # User B belongs to Org B, document belongs to Org A
        user_b = users_and_orgs["user_b"]
        api_client.force_authenticate(user=user_b)

        url = f"/api/v1/documents/{document_with_chunks.id}/generate/summary/"
        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Accès refusé" in response.data["detail"]

    def test_unauthenticated_generation_rejected(self, api_client, document_with_chunks):
        url = f"/api/v1/documents/{document_with_chunks.id}/generate/summary/"
        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_document_returns_404(self, api_client, users_and_orgs):
        user = users_and_orgs["user_a"]
        api_client.force_authenticate(user=user)

        fake_id = uuid.uuid4()
        url = f"/api/v1/documents/{fake_id}/generate/summary/"
        response = api_client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
