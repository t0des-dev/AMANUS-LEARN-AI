import json
import logging
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

from .base import AIProvider, AIResponse
from .mock_provider import MockAIProvider

logger = logging.getLogger(__name__)


class LocalLLMProvider(AIProvider):
    """Adapter for self-hosted local LLM endpoints (Ollama / vLLM / llama.cpp)."""

    name: str = "local"
    default_model: str = "llama3:8b"

    def __init__(
        self,
        base_url: str | None = None,
        default_model: str = "llama3:8b",
    ):
        self.base_url = (
            base_url or getattr(settings, "LOCAL_LLM_URL", "http://localhost:11434")
        ).rstrip("/")
        self.default_model = default_model
        self._fallback = MockAIProvider(model_name=default_model)

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int = 3000,
        response_format: str = "text",
    ) -> AIResponse:
        active_model = model or self.default_model
        url = f"{self.base_url}/api/generate"

        payload_dict: dict[str, Any] = {
            "model": active_model,
            "prompt": prompt,
            "system": system_instruction,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if response_format == "json":
            payload_dict["format"] = "json"

        payload = json.dumps(payload_dict).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data.get("response", "")

                input_tokens = data.get("prompt_eval_count", len(prompt.split()))
                output_tokens = data.get("eval_count", len(choice.split()))

                parsed_json = None
                if response_format == "json":
                    try:
                        parsed_json = json.loads(choice)
                    except json.JSONDecodeError:
                        pass

                return AIResponse(
                    content=choice,
                    parsed_json=parsed_json,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=active_model,
                    provider=self.name,
                )
        except Exception as e:
            logger.info(
                f"[LocalLLMProvider] Local endpoint unreachable ({e}); using mock fallback."
            )
            return self._fallback.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=active_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
