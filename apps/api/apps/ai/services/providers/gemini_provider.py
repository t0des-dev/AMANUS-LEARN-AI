import json
import logging
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

from .base import AIProvider, AIResponse
from .mock_provider import MockAIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """Adapter for Google Gemini models (gemini-1.5-flash, gemini-1.5-pro)."""

    name: str = "gemini"
    default_model: str = "gemini-1.5-flash"

    def __init__(self, api_key: str | None = None, default_model: str = "gemini-1.5-flash"):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "")
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
            logger.info("[GeminiProvider] No GEMINI_API_KEY; using mock fallback.")
            return self._fallback.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=active_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{active_model}:generateContent?key={self.api_key}"

        contents: list[dict[str, Any]] = []
        if system_instruction:
            contents.append(
                {
                    "role": "user",
                    "parts": [{"text": f"Instructions système : {system_instruction}"}],
                }
            )
            contents.append({"role": "model", "parts": [{"text": "Compris."}]})

        contents.append({"role": "user", "parts": [{"text": prompt}]})

        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if response_format == "json":
            generation_config["responseMimeType"] = "application/json"

        payload = json.dumps(
            {
                "contents": contents,
                "generationConfig": generation_config,
            }
        ).encode("utf-8")

        headers = {"Content-Type": "application/json"}

        try:
            req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data["candidates"][0]["content"]["parts"][0]["text"]
                usage = data.get("usageMetadata", {})
                input_tokens = usage.get("promptTokenCount", len(prompt.split()))
                output_tokens = usage.get("candidatesTokenCount", len(choice.split()))

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
            logger.warning(f"[GeminiProvider] API call failed ({e}); falling back to mock.")
            return self._fallback.generate(
                prompt=prompt,
                system_instruction=system_instruction,
                model=active_model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
            )
