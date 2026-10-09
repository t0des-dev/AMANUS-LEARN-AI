from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class AIResponse:
    """Standardized response from any AI generation provider."""

    content: str
    parsed_json: dict[str, Any] | list[Any] | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    provider: str = ""


class AIProviderError(Exception):
    """Raised when an AI provider fails during inference."""

    pass


class AIProvider(ABC):
    """Abstract base class for all LLM inference providers."""

    name: str = "base"
    default_model: str = "default"

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 3000,
        response_format: str = "text",  # "text" or "json"
    ) -> AIResponse:
        """Executes LLM inference and returns an AIResponse."""
        pass

    def stream_generate(
        self,
        prompt: str,
        system_instruction: str = "",
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 3000,
    ):
        """Streams text chunks or tokens from LLM inference.

        Default implementation calls generate and yields word tokens.
        """
        response = self.generate(
            prompt=prompt,
            system_instruction=system_instruction,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format="text",
        )
        content = response.content or ""
        tokens = content.split(" ")
        for idx, token in enumerate(tokens):
            yield token + (" " if idx < len(tokens) - 1 else "")

