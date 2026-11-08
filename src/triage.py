import time
from dataclasses import dataclass

from src.guardrails import Guardrails
from src.parsing import InvalidResponseError, parse_support_response
from src.prompts import Prompt, build_messages
from src.providers.base import LLMProvider, LLMResponse, TransientProviderError
from src.schema import SupportResponse, fallback_response


class TriageError(Exception):
    pass


@dataclass(frozen=True)
class TriageResult:
    response: SupportResponse
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    reported_cost_usd: float | None
    latency_s: float
    attempts: int
    invalid_responses: int = 0
    fallback: bool = False
    guardrail: tuple[str, ...] | None = None


@dataclass
class _Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reported_cost_usd: float | None = None
    attempts: int = 0
    invalid_responses: int = 0

    def add(self, llm: LLMResponse) -> None:
        self.prompt_tokens += llm.prompt_tokens
        self.completion_tokens += llm.completion_tokens
        self.attempts += llm.attempts
        if llm.reported_cost_usd is not None:
            self.reported_cost_usd = (self.reported_cost_usd or 0.0) + llm.reported_cost_usd


def triage(
    query: str,
    provider: LLMProvider,
    prompt: Prompt,
    max_parse_retries: int,
    guardrails: Guardrails | None = None,
) -> TriageResult:
    started = time.perf_counter()
    if not query.strip():
        raise TriageError("la consulta está vacía")
    text, rules = query, ()
    if guardrails is not None:
        screen = guardrails.screen_input(query)
        if screen.blocked:
            return _result(fallback_response(), provider, _Usage(), started, fallback=True, rules=screen.rules)
        text, rules = screen.text, screen.rules
    system, messages = build_messages(prompt, text)
    usage = _Usage()
    response = _ask_model(provider, system, messages, max_parse_retries, usage)
    if response is None:
        return _result(fallback_response(), provider, usage, started, fallback=True, rules=rules)
    return _result(response, provider, usage, started, fallback=False, rules=rules)


def _ask_model(
    provider: LLMProvider,
    system: str,
    messages: list[dict[str, str]],
    max_parse_retries: int,
    usage: _Usage,
) -> SupportResponse | None:
    schema = SupportResponse.model_json_schema()
    for _ in range(max_parse_retries + 1):
        try:
            llm = provider.complete(system, messages, schema)
        except TransientProviderError as error:
            usage.attempts += error.attempts
            return None
        usage.add(llm)
        try:
            return parse_support_response(llm.text)
        except InvalidResponseError as error:
            usage.invalid_responses += 1
            messages = [*messages, *_correction_turn(llm.text, error)]
    return None


def _correction_turn(text: str, error: InvalidResponseError) -> list[dict[str, str]]:
    return [
        {"role": "assistant", "content": text.strip() or "(respuesta vacía)"},
        {
            "role": "user",
            "content": (
                f"Tu respuesta no cumple el contrato ({error}). Respondé de nuevo con un único "
                "objeto JSON corregido, sin texto fuera del JSON."
            ),
        },
    ]


def _result(
    response: SupportResponse,
    provider: LLMProvider,
    usage: _Usage,
    started: float,
    fallback: bool,
    rules: tuple[str, ...],
) -> TriageResult:
    return TriageResult(
        response=response,
        provider=provider.name,
        model=provider.model,
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        reported_cost_usd=usage.reported_cost_usd,
        latency_s=round(time.perf_counter() - started, 3),
        attempts=usage.attempts,
        invalid_responses=usage.invalid_responses,
        fallback=fallback,
        guardrail=rules or None,
    )
