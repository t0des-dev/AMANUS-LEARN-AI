import math
import uuid

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.ai.services import (
    CitationBuilder,
    ContextBuilder,
    DeterministicEmbeddingProvider,
    Reranker,
    get_embedding_provider,
)
from apps.documents.models import Document
from apps.ingestion.models import DocumentChunk, DocumentPage
from apps.organizations.models import Organization, OrganizationMember, RoleChoices

User = get_user_model()


class EmbeddingProviderTests(APITestCase):
    """Unit tests for the abstract EmbeddingProvider layer."""

    def setUp(self):
        self.provider = DeterministicEmbeddingProvider(dimensions=1536)

    def test_embedding_dimensions_and_normalization(self):
        vec = self.provider.embed_text("Introduction aux architectures Transformers.")
        self.assertEqual(len(vec), 1536)

        # Check L2 unit normalization (norm ≈ 1.0)
        norm = math.sqrt(sum(x * x for x in vec))
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_semantic_similarity_concept(self):
        """Texts with related terms have higher cosine similarity than unrelated texts."""
        v_ai_1 = self.provider.embed_text(
            "Apprentissage profond et réseaux de neurones convolutionnels."
        )
        v_ai_2 = self.provider.embed_text(
            "Réseaux de neurones et apprentissage profond pour la vision."
        )
        v_unrelated = self.provider.embed_text(
            "Recette de cuisine traditionnelle italienne aux tomates fraîches."
        )

        def dot(a, b):
            return sum(x * y for x, y in zip(a, b))

        sim_related = dot(v_ai_1, v_ai_2)
        sim_unrelated = dot(v_ai_1, v_unrelated)

        self.assertGreater(sim_related, sim_unrelated)

    def test_get_embedding_provider_factory(self):
        provider = get_embedding_provider()
        self.assertIsNotNone(provider)
        self.assertEqual(provider.dimensions, 1536)


class ContextAndCitationBuilderTests(APITestCase):
    """Unit tests for ContextBuilder and CitationBuilder provenance preservation."""

    def test_citation_builder_preserves_full_provenance(self):
        builder = CitationBuilder()
        sample_results = [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "document_title": "Manuel IA",
                "page": 3,
                "chapter": "Chapitre 1 : Introduction",
                "section": "1.1 Notions",
                "subsection": "1.1.1 Historique",
                "content": "Le perceptron de Frank Rosenblatt est apparu en 1957.",
                "score": 0.94,
            }
        ]

        citations = builder.build_citations(sample_results)
        self.assertEqual(len(citations), 1)
        cit = citations[0]

        self.assertEqual(cit["citation_id"], 1)
        self.assertEqual(cit["document_title"], "Manuel IA")
        self.assertEqual(cit["page"], 3)
        self.assertEqual(cit["chapter"], "Chapitre 1 : Introduction")
        self.assertEqual(cit["section"], "1.1 Notions")
        self.assertIn("perceptron", cit["snippet"])
        self.assertEqual(cit["score"], 0.94)

        summary = builder.format_sources_summary(citations)
        self.assertIn("Manuel IA", summary)
        self.assertIn("Page 3", summary)

    def test_context_builder_includes_headers_and_anti_hallucination_rule(self):
        builder = ContextBuilder()
        sample_results = [
            {
                "chunk_id": str(uuid.uuid4()),
                "document_id": str(uuid.uuid4()),
                "document_title": "Guide Deep Learning",
                "page": 2,
                "chapter": "Chapitre 2",
                "section": "2.1 Optimiseurs",
                "content": "Adam combine RMSprop et la descente de gradient avec momentum.",
            }
        ]

        context = builder.build_context(sample_results)
        self.assertIn("Guide Deep Learning", context)
        self.assertIn("Chapitre: Chapitre 2", context)
        self.assertIn("Page: 2", context)
        self.assertIn("Adam combine RMSprop", context)

        prompt = builder.build_rag_prompt("Comment fonctionne Adam ?", context)
        self.assertIn("Cette information n'est pas présente dans les documents disponibles", prompt)
        self.assertIn("Comment fonctionne Adam ?", prompt)


class RerankerTests(APITestCase):
    """Unit tests for Reranker with lexical and structural boosts."""

    def test_reranker_boosts_matching_chapter_and_keywords(self):
        reranker = Reranker(vector_weight=0.5, lexical_weight=0.5)
        candidates = [
            {
                "content": "Description générale des paramètres de configuration du système.",
                "chapter": "Chapitre Généralités",
                "section": "Divers",
                "score": 0.80,
            },
            {
                "content": "Le modèle du perceptron multicouche utilise la rétropropagation du gradient.",
                "chapter": "Chapitre 3 : Réseaux de neurones",
                "section": "3.2 Le Perceptron",
                "score": 0.75,
            },
        ]

        # Query specifically targeting perceptron
        reranked = reranker.rerank("perceptron réseau neurone", candidates, top_k=2)
        self.assertEqual(len(reranked), 2)
        # Second candidate should be boosted to top position due to high lexical and heading match
        self.assertIn("perceptron", reranked[0]["content"])
        self.assertGreater(reranked[0]["score"], reranked[1]["score"])


class RAGPipelineAndAPITests(APITestCase):
    """Integration and Multi-Tenant Isolation tests for /api/v1/rag/* endpoints."""

    def setUp(self):
        self.embedding_provider = get_embedding_provider()

        # Tenant A: Alice in Org A
        self.user_a = User.objects.create_user(
            email="alice@tenant-a.com",
            password="PasswordA123!",
            first_name="Alice",
        )
        self.org_a = Organization.objects.create(name="Organization Alpha")
        self.member_a = OrganizationMember.objects.create(
            organization=self.org_a,
            user=self.user_a,
            role=RoleChoices.OWNER,
        )

        # Document and Chunks for Org A
        self.doc_a = Document.objects.create(
            organization=self.org_a,
            owner=self.user_a,
            title="Manuel de Deep Learning Alpha",
            file_name="manuel_alpha.txt",
            file_type="txt",
            file_size=1500,
            storage_key="test/alpha.txt",
        )
        self.page_a = DocumentPage.objects.create(
            document=self.doc_a,
            page_number=1,
            text="Chapitre 1 : Les Transformers\n\nL'architecture Transformer repose sur le mécanisme d'attention.",
            metadata={"chapter": "Chapitre 1 : Les Transformers", "section": "1.1 Attention"},
        )
        self.chunk_a1 = DocumentChunk.objects.create(
            document=self.doc_a,
            page=self.page_a,
            chunk_index=0,
            content="L'attention multi-têtes (Multi-Head Attention) permet au modèle de projeter conjointement l'information.",
            token_count=18,
            metadata={
                "document_id": str(self.doc_a.id),
                "document_title": self.doc_a.title,
                "page_number": 1,
                "chapter": "Chapitre 1 : Les Transformers",
                "section": "1.1 Attention",
            },
            embedding=self.embedding_provider.embed_text(
                "L'attention multi-têtes (Multi-Head Attention) permet au modèle de projeter conjointement l'information."
            ),
        )

        # Tenant B: Bob in Org B
        self.user_b = User.objects.create_user(
            email="bob@tenant-b.com",
            password="PasswordB123!",
            first_name="Bob",
        )
        self.org_b = Organization.objects.create(name="Organization Beta")
        self.member_b = OrganizationMember.objects.create(
            organization=self.org_b,
            user=self.user_b,
            role=RoleChoices.OWNER,
        )

        # Document and Chunks for Org B
        self.doc_b = Document.objects.create(
            organization=self.org_b,
            owner=self.user_b,
            title="Gestion Financière Beta",
            file_name="finance_beta.txt",
            file_type="txt",
            file_size=1200,
            storage_key="test/beta.txt",
        )
        self.page_b = DocumentPage.objects.create(
            document=self.doc_b,
            page_number=1,
            text="Chapitre 1 : Comptabilité analytique",
            metadata={"chapter": "Chapitre 1 : Comptabilité analytique"},
        )
        self.chunk_b1 = DocumentChunk.objects.create(
            document=self.doc_b,
            page=self.page_b,
            chunk_index=0,
            content="Le calcul du seuil de rentabilité nécessite de distinguer les charges fixes et variables.",
            token_count=17,
            metadata={
                "document_id": str(self.doc_b.id),
                "document_title": self.doc_b.title,
                "page_number": 1,
                "chapter": "Chapitre 1 : Comptabilité analytique",
            },
            embedding=self.embedding_provider.embed_text(
                "Le calcul du seuil de rentabilité nécessite de distinguer les charges fixes et variables."
            ),
        )

    def authenticate_as(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

    # =========================================================================
    # Strict Multi-Tenant Isolation Tests (Absolute Core Requirement)
    # =========================================================================

    def test_user_cannot_search_other_organization_chunks(self):
        """User B querying Org A returns 403 Forbidden."""
        self.authenticate_as(self.user_b)

        res = self.client.post(
            reverse("v1:rag:rag-search"),
            {
                "query": "Attention multi-têtes",
                "organization_id": str(self.org_a.id),
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Accès refusé", res.data["detail"])

    def test_search_results_strictly_scoped_to_own_organization(self):
        """When User B searches in Org B, Org A's chunks are NEVER returned."""
        self.authenticate_as(self.user_b)

        # Bob searches for Transformers (which only exists in Org A)
        res = self.client.post(
            reverse("v1:rag:rag-search"),
            {
                "query": "Attention multi-têtes Transformers",
                "organization_id": str(self.org_b.id),
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # None of the results belong to Org A
        returned_doc_ids = [r["document_id"] for r in res.data["results"]]
        self.assertNotIn(str(self.doc_a.id), returned_doc_ids)
        for r in res.data["results"]:
            self.assertEqual(r["document_id"], str(self.doc_b.id))

    def test_cross_tenant_document_filter_rejected(self):
        """Specifying document_id belonging to another tenant returns 404."""
        self.authenticate_as(self.user_a)

        res = self.client.post(
            reverse("v1:rag:rag-search"),
            {
                "query": "Gestion financière",
                "organization_id": str(self.org_a.id),
                "document_id": str(self.doc_b.id),  # Org B's doc
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # =========================================================================
    # RAG Search & Query API Functionality Tests
    # =========================================================================

    def test_post_rag_search_success(self):
        """POST /api/v1/rag/search/ returns relevant chunks with preserved metadata."""
        self.authenticate_as(self.user_a)

        res = self.client.post(
            reverse("v1:rag:rag-search"),
            {
                "query": "Comment fonctionne l'attention multi-têtes ?",
                "organization_id": str(self.org_a.id),
                "top_k": 3,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["query"], "Comment fonctionne l'attention multi-têtes ?")
        self.assertEqual(res.data["count"], 1)

        result_item = res.data["results"][0]
        self.assertEqual(result_item["chunk_id"], str(self.chunk_a1.id))
        self.assertEqual(result_item["document_id"], str(self.doc_a.id))
        self.assertEqual(result_item["document_title"], "Manuel de Deep Learning Alpha")
        self.assertEqual(result_item["page"], 1)
        self.assertEqual(result_item["chapter"], "Chapitre 1 : Les Transformers")
        self.assertEqual(result_item["section"], "1.1 Attention")
        self.assertIn("Multi-Head Attention", result_item["content"])
        self.assertGreater(result_item["score"], 0.2)

    def test_post_rag_query_success(self):
        """POST /api/v1/rag/query/ returns context, citations, and structured sources."""
        self.authenticate_as(self.user_a)

        res = self.client.post(
            reverse("v1:rag:rag-query"),
            {
                "query": "Explique le mécanisme d'attention",
                "organization_id": str(self.org_a.id),
                "top_k": 3,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("context", res.data)
        self.assertIn("citations", res.data)
        self.assertIn("prompt", res.data)
        self.assertIn("sources_summary", res.data)

        # Verify context contains grounded source markers
        self.assertIn("Manuel de Deep Learning Alpha", res.data["context"])
        self.assertIn("Source [1]", res.data["context"])

        # Verify citation structure
        self.assertEqual(len(res.data["citations"]), 1)
        cit = res.data["citations"][0]
        self.assertEqual(cit["document_id"], str(self.doc_a.id))
        self.assertEqual(cit["page"], 1)
        self.assertEqual(cit["chapter"], "Chapitre 1 : Les Transformers")
        self.assertEqual(cit["section"], "1.1 Attention")
        self.assertEqual(cit["chunk_id"], str(self.chunk_a1.id))

    def test_search_validation_errors(self):
        """Invalid requests (missing org, empty query) return 400 Bad Request."""
        self.authenticate_as(self.user_a)

        # Missing organization_id
        res_no_org = self.client.post(
            reverse("v1:rag:rag-search"),
            {"query": "Test query"},
            format="json",
        )
        self.assertEqual(res_no_org.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("organization_id", res_no_org.data)

        # Query too short
        res_short = self.client.post(
            reverse("v1:rag:rag-search"),
            {"query": "a", "organization_id": str(self.org_a.id)},
            format="json",
        )
        self.assertEqual(res_short.status_code, status.HTTP_400_BAD_REQUEST)
