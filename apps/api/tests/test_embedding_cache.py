from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import SimpleTestCase

from apps.ai.services.embeddings import get_embedding_provider, reset_embedding_provider
from apps.ai.services.embeddings.base import EmbeddingProvider
from apps.ai.services.embeddings.cache_provider import CachedEmbeddingProvider


class CachedEmbeddingProviderTests(SimpleTestCase):
    """Verifies read-through caching semantics and best-effort resilience."""

    def setUp(self):
        cache.clear()
        self.inner = MagicMock(spec=EmbeddingProvider)
        self.inner.dimensions = 4
        self.inner.model_name = "test-model"
        self.provider = CachedEmbeddingProvider(self.inner)

    def tearDown(self):
        cache.clear()

    def test_embed_text_hits_cache_on_second_call(self):
        self.inner.embed_text.return_value = [0.1, 0.2, 0.3, 0.4]

        first = self.provider.embed_text("les réseaux de neurones")
        second = self.provider.embed_text("les réseaux de neurones")

        self.assertEqual(first, [0.1, 0.2, 0.3, 0.4])
        self.assertEqual(second, first)
        self.inner.embed_text.assert_called_once()

    def test_different_texts_do_not_share_cache_entry(self):
        self.inner.embed_text.side_effect = [[1.0], [2.0]]

        a = self.provider.embed_text("texte alpha")
        b = self.provider.embed_text("texte beta")

        self.assertEqual(a, [1.0])
        self.assertEqual(b, [2.0])
        self.assertEqual(self.inner.embed_text.call_count, 2)

    def test_embed_batch_only_computes_misses(self):
        self.inner.embed_batch.return_value = [[0.5, 0.5]]

        # Prime the cache with one entry
        self.provider.embed_batch(["premier"])
        self.inner.embed_batch.reset_mock()

        # Second call: first text is a hit, second is a miss
        results = self.provider.embed_batch(["premier", "second"])

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], [0.5, 0.5])
        self.inner.embed_batch.assert_called_once_with(["second"])

    def test_cache_get_failure_falls_back_to_inner_provider(self):
        self.inner.embed_text.return_value = [9.9]

        with patch(
            "apps.ai.services.embeddings.cache_provider.cache.get",
            side_effect=ConnectionError("redis down"),
        ):
            vector = self.provider.embed_text("résilience")

        self.assertEqual(vector, [9.9])

    def test_cache_set_failure_does_not_break_embedding(self):
        self.inner.embed_text.return_value = [7.7]

        with patch(
            "apps.ai.services.embeddings.cache_provider.cache.set",
            side_effect=ConnectionError("redis down"),
        ):
            vector = self.provider.embed_text("résilience écriture")

        self.assertEqual(vector, [7.7])

    def test_factory_returns_cache_wrapped_provider(self):
        reset_embedding_provider()
        try:
            provider = get_embedding_provider()
            self.assertIsInstance(provider, CachedEmbeddingProvider)
            self.assertIs(provider, get_embedding_provider())
        finally:
            reset_embedding_provider()
