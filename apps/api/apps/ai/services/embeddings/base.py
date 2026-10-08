from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Abstract Base Class for text embedding generation.

    Decouples vector search from specific AI vendors (OpenAI, Local, Mock).
    """

    dimensions: int = 1536
    model_name: str = "text-embedding-3-small"

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generates a normalized embedding vector for a single string."""
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generates normalized embedding vectors for a batch of strings."""
        pass
