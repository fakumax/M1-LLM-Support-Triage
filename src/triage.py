import time
from dataclasses import dataclass

from pydantic import ValidationError

from src.prompts import Prompt, build_messages
from src.providers.base import LLMProvider, LLMResponse
from src.schema import SupportResponse


class TriageError(Exception):
    pass


@dataclass(frozen=True)
class TriageResult:
    response: SupportResponse
    llm: LLMResponse
    latency_s: float
    attempts: int
    fallback: bool = False
    guardrail: str | None = None


def triage(query: str, provider: LLMProvider, prompt: Prompt) -> TriageResult:
    started = time.perf_counter()
    if not query.strip():
        raise TriageError("la consulta está vacía")
    system, messages = build_messages(prompt, query)
    llm = provider.complete(system, messages, SupportResponse.model_json_schema())
    try:
        response = SupportResponse.model_validate_json(llm.text)
    except ValidationError as error:
        raise TriageError(f"la respuesta del modelo no cumple el contrato: {_describe(error)}") from error
    latency_s = time.perf_counter() - started
    return TriageResult(
        response=response,
        llm=llm,
        latency_s=round(latency_s, 3),
        attempts=llm.attempts,
    )


def _describe(error: ValidationError) -> str:
    fields = sorted({".".join(str(part) for part in item["loc"]) for item in error.errors() if item["loc"]})
    return ", ".join(fields) or "JSON inválido"
