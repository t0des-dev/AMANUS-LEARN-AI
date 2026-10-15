"""Native pgvector integration tests.

These tests exercise the real PostgreSQL + pgvector code path (CosineDistance
annotation, GIN trigram lexical index) instead of the in-memory SQLite fallback.

They are skipped automatically when the test database is SQLite (local runs),
and executed in CI where the pgvector/pg16 service is provided.
"""

import logging
from unittest import skipUnless

from django.db import connection
from rest_framework.test import APITestCase

from apps.ai.services import DeterministicEmbeddingProvider
from apps.ai.services.hybrid_search import HybridSearchService
from apps.ai.services.lexical_search import LexicalSearchService
from apps.ai.services.vector_search import VectorSearchService
from apps.documents.models import Document
from apps.ingestion.models import DocumentChunk, DocumentPage
from apps.organizations.models import Organization

IS_POSTGRES = connection.vendor == "postgresql"


@skipUnless(IS_POSTGRES, "Requires a PostgreSQL database with pgvector enabled")
class NativePgVectorSearchTests(APITestCase):
    """Verifies native pgvector CosineDistance search (no in-memory fallback)."""

    def setUp(self):
        self.embedding_provider = DeterministicEmbeddingProvider(dimensions=1536)

        self.org = Organization.objects.create(name="PgVector Org")
        self.doc = Document.objects.create(
            organization=self.org,
            owner=None,
            title="Manuel de Transformers",
            file_name="transformers.pdf",
            file_type="pdf",
            file_size=1024,
            storage_key="test/transformers.pdf",
        )
        self.page = DocumentPage.objects.create(
            document=self.doc,
            page_number=1,
            text="Le mécanisme d'attention régule les pondérations entre tokens.",
            metadata={"chapter": "Attention", "section": "1.1"},
        )

        self.attention_content = (
            "Le mécanisme d'attention multi-têtes projette l'information entre tokens."
        )
        self.cnn_content = (
            "Les réseaux convolutifs appliquent des filtres de convolution sur les images."
        )

        self.chunk_attention = DocumentChunk.objects.create(
            document=self.doc,
            page=self.page,
            chunk_index=0,
            content=self.attention_content,
            token_count=15,
            metadata={"page_number": 1, "chapter": "Attention"},
            embedding=self.embedding_provider.embed_text(self.attention_content),
        )
        self.chunk_cnn = DocumentChunk.objects.create(
            document=self.doc,
            page=self.page,
            chunk_index=1,
            content=self.cnn_content,
            token_count=15,
            metadata={"page_number": 1, "chapter": "Vision"},
            embedding=self.embedding_provider.embed_text(self.cnn_content),
        )

    def test_native_cosine_distance_used_and_orders_by_similarity(self):
        """The pgvector annotation path must run (not the fallback) and rank correctly."""
        service = VectorSearchService()
        query_vector = self.embedding_provider.embed_text(self.attention_content)

        with self.assertLogs("apps.ai.services.vector_search", level="WARNING") as log_output:
            results = service.search(
                query_vector=query_vector,
                organization_id=str(self.org.id),
                top_k=2,
            )

        # No fallback warning must have been emitted → native path succeeded
        fallback_logs = [r for r in log_output.output if "fallback" in r.lower()]
        self.assertEqual(fallback_logs, [], "Native pgvector path must not fall back to memory")

        self.assertEqual(len(results), 2)
        # Most similar chunk (same embedding) must rank first with near-perfect similarity
        self.assertEqual(results[0]["chunk_id"], str(self.chunk_attention.id))
        self.assertGreater(results[0]["score"], 0.99)
        self.assertLess(results[0]["score"], 1.0001)
        # Second result must be strictly less similar
        self.assertLess(results[1]["score"], results[0]["score"])

    def test_native_search_enforces_multi_tenant_isolation(self):
        """Chunks from another organization must never leak into native pgvector results."""
        other_org = Organization.objects.create(name="Intruder Org")
        other_doc = Document.objects.create(
            organization=other_org,
            owner=None,
            title="Doc Intrus",
            file_name="intruder.pdf",
            file_type="pdf",
            file_size=512,
            storage_key="test/intruder.pdf",
        )
        intruder_content = self.attention_content  # identical content → identical embedding
        DocumentChunk.objects.create(
            document=other_doc,
            chunk_index=0,
            content=intruder_content,
            token_count=15,
            embedding=self.embedding_provider.embed_text(intruder_content),
        )

        service = VectorSearchService()
        query_vector = self.embedding_provider.embed_text(self.attention_content)

        results = service.search(
            query_vector=query_vector,
            organization_id=str(self.org.id),
            top_k=10,
        )

        for r in results:
            self.assertNotEqual(r["document_id"], str(other_doc.id))
        self.assertTrue(all(r["chunk_id"] != "intruder" for r in results))
        self.assertEqual(
            {r["document_id"] for r in results}, {str(self.doc.id)}
        )


@skipUnless(IS_POSTGRES, "Requires a PostgreSQL database with pgvector enabled")
class NativeTrigramLexicalSearchTests(APITestCase):
    """Verifies lexical ILIKE search accelerated by the pg_trgm GIN index."""

    def setUp(self):
        self.org = Organization.objects.create(name="Trigram Org")
        self.doc = Document.objects.create(
            organization=self.org,
            owner=None,
            title="Algorithmes d'optimisation",
            file_name="optim.pdf",
            file_type="pdf",
            file_size=512,
            storage_key="test/optim.pdf",
        )
        self.chunk = DocumentChunk.objects.create(
            document=self.doc,
            chunk_index=0,
            content="La descente de gradient stochastique minimise la fonction de coût.",
            token_count=12,
            metadata={"page_number": 1},
        )
        DocumentChunk.objects.create(
            document=self.doc,
            chunk_index=1,
            content="Les réseaux de neurones récurrents traitent les séquences temporelles.",
            token_count=12,
            metadata={"page_number": 2},
        )

    def test_trigram_index_exists(self):
        """The GIN trigram index must have been created by migration 0002."""
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT indexname FROM pg_indexes "
                "WHERE indexname = 'ingestion_documentchunk_content_trgm';"
            )
            row = cursor.fetchone()
        self.assertIsNotNone(row, "pg_trgm GIN index is missing on DocumentChunk.content")

    def test_lexical_search_finds_stemmed_variant_via_ilike(self):
        """ILIKE matching must find a partial/inflected term (unindexed behavior check)."""
        service = LexicalSearchService()
        results = service.search(
            query="stochastique",
            organization_id=str(self.org.id),
            top_k=5,
        )
        self.assertTrue(results)
        self.assertEqual(results[0]["chunk_id"], str(self.chunk.id))

    def test_hybrid_search_returns_ranked_results(self):
        """Hybrid (dense + lexical, RRF) must merge both signals on Postgres."""
        embedding_provider = DeterministicEmbeddingProvider(dimensions=1536)
        query = "descente de gradient stochastique"
        DocumentChunk.objects.filter(pk=self.chunk.pk).update(
            embedding=embedding_provider.embed_text(self.chunk.content)
        )

        service = HybridSearchService()
        results = service.search(
            query=query,
            organization_id=str(self.org.id),
            top_k=5,
        )
        self.assertTrue(results)
        self.assertEqual(results[0]["chunk_id"], str(self.chunk.id))
        self.assertIn("score", results[0])

        logger = logging.getLogger("apps.ai.services.hybrid_search")
        self.assertIsNotNone(logger)
