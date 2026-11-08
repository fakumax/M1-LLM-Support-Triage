import time
from typing import Any

import httpx2
from google import genai
from google.genai import errors, types

from src.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderError,
    ProviderSettings,
    TransientProviderError,
    call_with_backoff,
    parse_retry_after,
)

PROVIDER_NAME = "gemini"
ROLES = {"user": "user", "assistant": "model"}
MS_PER_S = 1000


class GeminiProvider(LLMProvider):
    def __init__(self, settings: ProviderSettings) -> None:
        self._settings = settings
        self.name = PROVIDER_NAME
        self.model = settings.model
        self._client = genai.Client(
            api_key=settings.api_key,
            http_options=types.HttpOptions(
                timeout=round(settings.timeout_s * MS_PER_S),
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )

    def complete(self, system: str, messages: list[dict[str, str]], json_schema: dict[str, Any]) -> LLMResponse:
        return call_with_backoff(
            lambda: self._send(system, messages, json_schema),
            self._settings.max_api_retries,
            self._settings.max_retry_after_s,
        )

    def _send(self, system: str, messages: list[dict[str, str]], json_schema: dict[str, Any]) -> LLMResponse:
        started = time.perf_counter()
        response = self._generate(system, messages, json_schema)
        latency_s = time.perf_counter() - started
        prompt_tokens, completion_tokens = _token_counts(response)
        return LLMResponse(
            text=response.text or "",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_s=round(latency_s, 3),
            provider=PROVIDER_NAME,
            model=self._settings.model,
            reported_cost_usd=None,
        )

    def _generate(
        self, system: str, messages: list[dict[str, str]], json_schema: dict[str, Any]
    ) -> types.GenerateContentResponse:
        try:
            return self._client.models.generate_content(
                model=self._settings.model,
                contents=[_content(message) for message in messages],
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=self._settings.temperature,
                    max_output_tokens=self._settings.max_tokens,
                    response_mime_type="application/json",
                    response_json_schema=json_schema,
                ),
            )
        except errors.APIError as error:
            raise _from_api_error(error) from error
        except httpx2.TimeoutException as error:
            raise TransientProviderError("timeout con Gemini") from error
        except httpx2.TransportError as error:
            raise TransientProviderError("error de conexión con Gemini") from error
        except Exception as error:
            raise ProviderError(f"error del cliente de Gemini: {type(error).__name__}") from error


def _content(message: dict[str, str]) -> types.Content:
    return types.Content(role=ROLES[message["role"]], parts=[types.Part(text=message["content"])])


def _token_counts(response: types.GenerateContentResponse) -> tuple[int, int]:
    usage = response.usage_metadata
    if usage is None:
        return 0, 0
    thoughts = usage.thoughts_token_count or 0
    return usage.prompt_token_count or 0, (usage.candidates_token_count or 0) + thoughts


def _from_api_error(error: errors.APIError) -> ProviderError:
    message = f"Gemini respondió {error.code}: {error.message}"
    code = error.code or 0
    if code == 429 or code >= 500:
        return TransientProviderError(message, retry_after_s=_retry_after(error))
    return ProviderError(message)


def _retry_after(error: errors.APIError) -> float | None:
    headers = getattr(error.response, "headers", None)
    return parse_retry_after(headers.get("retry-after") if headers is not None else None)
