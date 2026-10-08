import json
import logging
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

from .base import AIProvider, AIResponse
from .mock_provider import MockAIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """Adapter for Anthropic Claude models (claude-3-5-sonnet, claude-3-haiku)."""

    name: str = "anthropic"
    default_model: str = "claude-3-5-sonnet-20241022"

    def __init__(
        self, api_key: str | None = None, default_model: str = "claude-3-5-sonnet-20241022"
    ):
        self.api_key = api_key or getattr(settings, "ANTHROPIC_API_KEY", "")
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

        if not self.api_key:
            logger.info("[AnthropicProvider] No ANTHROPIC_API_KEY; using mock fallback.")
            return self._fallback.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=active_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

        url = "https://api.anthropic.com/v1/messages"
        payload_dict: dict[str, Any] = {
            "model": active_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_instruction:
            payload_dict["system"] = system_instruction

        payload = json.dumps(payload_dict).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["content"][0]["text"]
                usage = data.get("usage", {})
                input_tokens = usage.get("input_tokens", len(prompt.split()))
                output_tokens = usage.get("output_tokens", len(choice.split()))

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
            logger.warning(f"[AnthropicProvider] API call failed ({e}); falling back to mock.")
            return self._fallback.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=active_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
