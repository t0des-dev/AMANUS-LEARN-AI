import json
import logging
import urllib.error
import urllib.request
from typing import Sequence

from django.conf import settings

from .base import EmbeddingProvider
from .mock_provider import DeterministicEmbeddingProvider

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Adapter for OpenAI text embedding API (e.g. text-embedding-3-small)."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "text-embedding-3-small",
        dimensions: int = 1536,
    ):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
        self.model_name = model_name
        self.dimensions = dimensions
        self._fallback = DeterministicEmbeddingProvider(dimensions=dimensions)

    def embed_text(self, text: str) -> list[float]:
        batch = self.embed_batch([text])
        return batch[0] if batch else [0.0] * self.dimensions

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        if not self.api_key:
            logger.info(
                "[OpenAIEmbeddingProvider] No OPENAI_API_KEY set; falling back to deterministic provider."
            )
            return self._fallback.embed_batch(texts)

        url = "https://api.openai.com/v1/embeddings"
        payload = json.dumps({"input": list(texts), "model": self.model_name}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # Sort by index in case returned out of order
                results = sorted(data.get("data", []), key=lambda x: x.get("index", 0))
                return [r["embedding"] for r in results]
        except Exception as e:
            logger.warning(f"[OpenAIEmbeddingProvider] API call failed ({e}); using fallback.")
            return self._fallback.embed_batch(texts)
