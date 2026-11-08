import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    latency_s: float
    provider: str
    model: str
    reported_cost_usd: float | None
    attempts: int = 1
    cached: bool = False


@dataclass(frozen=True)
class ProviderSettings:
    api_key: str = field(repr=False)
    model: str
    base_url: str | None
    temperature: float
    max_tokens: int
    timeout_s: float
    max_api_retries: int
    max_retry_after_s: float


class ProviderError(Exception):
    pass


class TransientProviderError(ProviderError):
    def __init__(self, message: str, retry_after_s: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s
        self.attempts = 1


class LLMProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def complete(self, system: str, messages: list[dict[str, str]], json_schema: dict[str, Any]) -> LLMResponse:
        ...


def parse_retry_after(value: str | None) -> float | None:
    try:
        return float(value) if value else None
    except ValueError:
        return None


def backoff_delay(attempt: int, max_retry_after_s: float, retry_after_s: float | None = None) -> float:
    if retry_after_s is not None:
        return min(retry_after_s, max_retry_after_s)
    return float(2**attempt)


def call_with_backoff(
    call: Callable[[], LLMResponse],
    max_api_retries: int,
    max_retry_after_s: float,
    sleep: Callable[[float], None] = time.sleep,
) -> LLMResponse:
    attempt = 0
    while True:
        try:
            response = call()
        except TransientProviderError as error:
            if attempt >= max_api_retries:
                error.attempts = attempt + 1
                raise
            sleep(backoff_delay(attempt, max_retry_after_s, error.retry_after_s))
            attempt += 1
        else:
            return replace(response, attempts=attempt + 1)
