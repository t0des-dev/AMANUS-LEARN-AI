import json
import logging
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

from .base import AIProvider, AIResponse
from .mock_provider import MockAIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """Adapter for OpenAI models (gpt-4o, gpt-4o-mini)."""

    name: str = "openai"
    default_model: str = "gpt-4o-mini"

    def __init__(self, api_key: str | None = None, default_model: str = "gpt-4o-mini"):
        self.api_key = api_key or getattr(settings, "OPENAI_API_KEY", "")
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
            logger.info(
                "[OpenAIProvider] No OPENAI_API_KEY provided; falling back to Mock provider."
            )
            return self._fallback.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=active_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

        url = "https://api.openai.com/v1/chat/completions"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload_dict: dict[str, Any] = {
            "model": active_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format == "json":
            payload_dict["response_format"] = {"type": "json_object"}

        payload = json.dumps(payload_dict).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                input_tokens = usage.get("prompt_tokens", len(prompt.split()))
                output_tokens = usage.get("completion_tokens", len(choice.split()))

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
            logger.warning(f"[OpenAIProvider] OpenAI API call failed ({e}); falling back to mock.")
            return self._fallback.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=active_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
