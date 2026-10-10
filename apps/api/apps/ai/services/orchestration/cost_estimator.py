import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


# Published provider pricing benchmarks (USD per 1,000,000 tokens)
LLM_PRICING_PER_MILLION_TOKENS = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    # Anthropic
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    # Google Gemini
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    # Local & Mock
    "mock": {"input": 0.00, "output": 0.00},
    "local": {"input": 0.00, "output": 0.00},
}

# TTS Pricing benchmarks (USD per 1,000 characters)
TTS_PRICING_PER_THOUSAND_CHARS = {
    "openai": 0.015,  # standard tts-1 is $0.015 / 1k chars
    "openai-hd": 0.030,  # tts-1-hd is $0.030 / 1k chars
    "elevenlabs": 0.150,  # ElevenLabs standard tier ~ $0.15 / 1k chars
    "mock": 0.000,
}


class CostEstimator:
    """Estimates and audits AI consumption costs transparently.

    Distinguishes measured telemetry (tokens, characters, duration) from estimated costs.
    Never fabricates values or logs secrets.
    """

    @classmethod
    def estimate_llm_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculates estimated cost in USD based on measured token counts."""
        if not model:
            return 0.0
        model_key = str(model).lower().strip()
        rates = LLM_PRICING_PER_MILLION_TOKENS.get(model_key)

        if not rates:
            # Match prefixes
            for key, val in LLM_PRICING_PER_MILLION_TOKENS.items():
                if key in model_key or model_key in key:
                    rates = val
                    break

        if not rates:
            # Fallback to general small model rates
            rates = LLM_PRICING_PER_MILLION_TOKENS["gpt-4o-mini"]

        cost_in = (input_tokens / 1_000_000.0) * rates["input"]
        cost_out = (output_tokens / 1_000_000.0) * rates["output"]
        return round(cost_in + cost_out, 6)

    @classmethod
    def estimate_tts_cost(cls, voice_provider: str, character_count: int) -> float:
        """Calculates estimated cost in USD based on character volume for TTS."""
        provider_key = str(voice_provider).lower().strip()
        rate_per_k = TTS_PRICING_PER_THOUSAND_CHARS.get(provider_key, 0.0)
        return round((character_count / 1_000.0) * rate_per_k, 6)

    @classmethod
    def build_observability_summary(
        cls,
        provider: str,
        model: str,
        duration_seconds: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        characters: int = 0,
        attempts: int = 1,
        error_category: str | None = None,
    ) -> dict[str, Any]:
        """Constructs sanitized observability audit metrics dictionary."""
        is_tts = characters > 0 and (input_tokens == 0 and output_tokens == 0)
        if is_tts:
            estimated_cost = cls.estimate_tts_cost(provider, characters)
        else:
            estimated_cost = cls.estimate_llm_cost(model, input_tokens, output_tokens)

        return {
            "provider": str(provider),
            "model": str(model),
            "duration_seconds": round(duration_seconds, 3),
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "total_tokens": int(input_tokens + output_tokens),
            "characters_processed": int(characters),
            "attempts_count": int(attempts),
            "estimated_cost_usd": estimated_cost,
            "is_cost_estimated": True,
            "error_category": error_category,
            "timestamp": time.time(),
        }
