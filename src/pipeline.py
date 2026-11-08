import sys
from dataclasses import dataclass
from typing import Any

from src.config import load_models_config
from src.guardrails import Guardrails
from src.metrics import METRICS_FILE, MetricsError, append_metrics, build_record
from src.prompts import Prompt, load_prompt
from src.providers import get_provider
from src.providers.base import LLMProvider
from src.triage import TriageResult, triage


@dataclass(frozen=True)
class TriageDeps:
    provider: LLMProvider
    prompt: Prompt
    max_parse_retries: int
    guardrails: Guardrails | None = None


def build_triage_deps(
    provider_name: str, model: str | None, prompt_version: str, with_guardrails: bool = True
) -> TriageDeps:
    config = load_models_config()
    return TriageDeps(
        provider=get_provider(provider_name, model),
        prompt=load_prompt(prompt_version),
        max_parse_retries=config["defaults"]["max_parse_retries"],
        guardrails=_guardrails(config["guardrails"]) if with_guardrails else None,
    )


def _guardrails(settings: dict[str, Any]) -> Guardrails:
    return Guardrails(canary=settings["canary"], max_query_chars=settings["max_query_chars"])


def triage_and_register(query: str, deps: TriageDeps, source: str) -> tuple[TriageResult, dict[str, Any] | None]:
    result = triage(query, deps.provider, deps.prompt, deps.max_parse_retries, deps.guardrails)
    try:
        record = build_record(result, source=source, prompt_version=deps.prompt.version)
        append_metrics(record, METRICS_FILE)
    except MetricsError as error:
        print(f"Aviso: no se registraron las métricas: {error}", file=sys.stderr)
        return result, None
    if record["cost_usd"] is None:
        print(
            f"Aviso: {result.model} no tiene precio en config/models.yaml; cost_usd queda en null",
            file=sys.stderr,
        )
    return result, record
