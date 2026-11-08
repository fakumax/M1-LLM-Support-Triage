import sys
from dataclasses import dataclass
from typing import Any

from src.cache import CachedProvider
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
    provider_name: str,
    model: str | None,
    prompt_version: str,
    with_guardrails: bool = True,
    with_cache: bool = False,
) -> TriageDeps:
    config = load_models_config()
    defaults = config["defaults"]
    provider = get_provider(provider_name, model)
    if with_cache:
        provider = CachedProvider(provider, temperature=defaults["temperature"], max_tokens=defaults["max_tokens"])
    return TriageDeps(
        provider=provider,
        prompt=load_prompt(prompt_version),
        max_parse_retries=defaults["max_parse_retries"],
        guardrails=_guardrails(config["guardrails"]) if with_guardrails else None,
    )


def _guardrails(settings: dict[str, Any]) -> Guardrails:
    return Guardrails(canary=settings["canary"], max_query_chars=settings["max_query_chars"])


def triage_and_register(query: str, deps: TriageDeps, source: str) -> tuple[TriageResult, dict[str, Any]]:
    result = triage(query, deps.provider, deps.prompt, deps.max_parse_retries, deps.guardrails)
    record = build_record(result, source=source, prompt_version=deps.prompt.version)
    try:
        append_metrics(record, METRICS_FILE)
    except MetricsError as error:
        print(f"Aviso: no se registraron las métricas: {error}", file=sys.stderr)
    return result, record
