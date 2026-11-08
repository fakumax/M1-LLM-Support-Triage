import time
from typing import Any

import openai

from src.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderError,
    ProviderSettings,
    TransientProviderError,
    call_with_backoff,
)

PROVIDER_NAME = "openrouter"


class OpenRouterProvider(LLMProvider):
    def __init__(self, settings: ProviderSettings) -> None:
        self._settings = settings
        self.name = PROVIDER_NAME
        self.model = settings.model
        self._client = openai.OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=settings.timeout_s,
            max_retries=0,
            default_headers={"X-Title": "llm-support-triage"},
        )

    def complete(self, system: str, messages: list[dict[str, str]], json_schema: dict[str, Any]) -> LLMResponse:
        return call_with_backoff(
            lambda: self._send(system, messages, json_schema),
            self._settings.max_api_retries,
            self._settings.max_retry_after_s,
        )

    def _send(self, system: str, messages: list[dict[str, str]], json_schema: dict[str, Any]) -> LLMResponse:
        started = time.perf_counter()
        try:
            response = self._client.chat.completions.create(
                model=self._settings.model,
                messages=[{"role": "system", "content": system}, *messages],
                temperature=self._settings.temperature,
                max_tokens=self._settings.max_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": "support_response", "strict": True, "schema": json_schema},
                },
            )
        except (openai.RateLimitError, openai.InternalServerError) as error:
            raise TransientProviderError(
                f"OpenRouter respondió {error.status_code}",
                retry_after_s=_retry_after_seconds(error),
            ) from error
        except openai.APIConnectionError as error:
            raise TransientProviderError("timeout o error de conexión con OpenRouter") from error
        except openai.APIStatusError as error:
            raise ProviderError(f"OpenRouter respondió {error.status_code}: {error.message}") from error
        except openai.OpenAIError as error:
            raise ProviderError(f"error del cliente de OpenRouter: {error}") from error

        latency_s = time.perf_counter() - started
        content = response.choices[0].message.content if response.choices else None
        usage = response.usage
        extra = (usage.model_extra or {}) if usage else {}
        cost = extra.get("cost")
        return LLMResponse(
            text=content or "",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            latency_s=round(latency_s, 3),
            provider=PROVIDER_NAME,
            model=self._settings.model,
            reported_cost_usd=float(cost) if cost is not None else None,
        )


def _retry_after_seconds(error: openai.APIStatusError) -> float | None:
    value = error.response.headers.get("retry-after")
    try:
        return float(value) if value else None
    except ValueError:
        return None
