import hashlib
import math
from typing import Sequence

from .base import EmbeddingProvider


class DeterministicEmbeddingProvider(EmbeddingProvider):
    """Deterministic local embedding provider for tests and offline development.

    Produces unit-normalized 1536-dimensional vectors where texts sharing tokens
    exhibit high cosine similarity.
    """

    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions
        self.model_name = "mock-deterministic-1536"

    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            # Return normalized zero/uniform vector
            val = 1.0 / math.sqrt(self.dimensions)
            return [val] * self.dimensions

        vector = [0.0] * self.dimensions
        words = text.lower().split()

        for word in words:
            # Deterministic hash to dimension bucket
            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            primary_idx = h % self.dimensions
            secondary_idx = (h >> 16) % self.dimensions

            # Sign for pseudo-random projection
            sign = 1.0 if ((h >> 32) & 1) else -1.0
            vector[primary_idx] += sign * 1.0
            vector[secondary_idx] += sign * 0.5

        # Also blend overall string hash
        doc_hash = int(hashlib.md5(text.encode("utf-8")).hexdigest(), 16)
        for offset in range(min(self.dimensions, 64)):
            vector[offset] += 0.1 * math.sin((doc_hash + offset))

        # Normalize to unit length (L2 norm)
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0.0:
            norm = 1.0

        return [x / norm for x in vector]

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]
