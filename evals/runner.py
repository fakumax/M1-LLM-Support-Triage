import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from evals.report import RunInfo, build_payload, render_markdown, save_reports
from evals.scoring import CaseOutcome, summarize
from src.config import ROOT_DIR, load_env, load_models_config
from src.pipeline import TriageDeps, build_triage_deps, triage_and_register
from src.prompts import PromptError
from src.providers import PROVIDERS
from src.providers.base import ProviderError
from src.schema import CATEGORIES
from src.triage import TriageError, TriageResult

DATASET_FILE = ROOT_DIR / "evals" / "dataset.jsonl"
RESULTS_DIR = ROOT_DIR / "evals" / "results"
EVAL_SOURCE = "eval"
FREE_MODEL_SUFFIX = ":free"


class EvalError(Exception):
    pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_models_config()["defaults"]
    parser = argparse.ArgumentParser(description="Corre la suite de evals y reporta métricas.")
    parser.add_argument("--provider", default=defaults["provider"], choices=sorted(PROVIDERS))
    parser.add_argument("--model", help="ID del modelo (por defecto, el de config/models.yaml)")
    parser.add_argument("--prompt", default=defaults["prompt_version"], help="versión del prompt, por ejemplo v1")
    parser.add_argument("--dataset", type=Path, default=DATASET_FILE, help="dataset JSONL a evaluar")
    parser.add_argument("--limit", type=int, help="evalúa solo los primeros N casos; no guarda reportes")
    parser.add_argument("--sleep", type=float, help="segundos entre requests (por defecto, según el proveedor)")
    parser.add_argument("--no-guardrails", action="store_true", help="desactiva los guardrails de entrada y salida")
    parser.add_argument("--cache", action="store_true", help="reutiliza respuestas de data/cache/ sin llamar a la API")
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error("--limit tiene que ser al menos 1")
    if args.sleep is not None and args.sleep < 0:
        parser.error("--sleep no puede ser negativo")
    return args


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    load_env()
    args = parse_args(argv)
    started = datetime.now()
    try:
        deps = build_triage_deps(
            args.provider,
            args.model,
            args.prompt,
            with_guardrails=not args.no_guardrails,
            with_cache=args.cache,
        )
        _require_free_model(deps.provider.name, deps.provider.model)
        sleep_s = _sleep_s(deps.provider.name, args.sleep)
        dataset = args.dataset.resolve()
        cases = load_dataset(dataset)[: args.limit]
        base = result_base(
            started,
            deps.provider.name,
            deps.provider.model,
            deps.prompt.version,
            deps.guardrails is not None,
            dataset,
        )
        if args.limit is None and (RESULTS_DIR / f"{base}.json").exists():
            raise EvalError(f"ya existe el reporte {base}.json; esperá un minuto y volvé a correr")
        outcomes = run_cases(cases, deps, sleep_s)
    except (ProviderError, TriageError, PromptError, EvalError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    info = RunInfo(
        timestamp=started.isoformat(timespec="seconds"),
        provider=deps.provider.name,
        model=deps.provider.model,
        prompt_version=deps.prompt.version,
        dataset=_display_path(dataset),
        sleep_s=sleep_s,
        guardrails=deps.guardrails is not None,
        cache=args.cache,
    )
    summary = summarize(outcomes)
    markdown = render_markdown(info, summary, outcomes)
    print(markdown.rstrip())
    if args.limit is not None:
        print("Corrida parcial (--limit): no se guardaron reportes en evals/results/.", file=sys.stderr)
        return 0
    json_path, md_path = save_reports(RESULTS_DIR, base, build_payload(info, summary, outcomes), markdown)
    print(f"Reportes guardados: {json_path} y {md_path}", file=sys.stderr)
    return 0


def load_dataset(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise EvalError(f"no existe el dataset {_display_path(path)}")
    cases: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as file:
        for number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
                expected = case["expected_category"]
            except (json.JSONDecodeError, KeyError) as error:
                raise EvalError(f"{path.name} línea {number} no es un caso válido") from error
            if expected not in CATEGORIES:
                raise EvalError(f"{path.name} línea {number}: categoría esperada inválida ({expected})")
            cases.append(case)
    if not cases:
        raise EvalError(f"{path.name} no tiene casos")
    return cases


def run_cases(cases: list[dict[str, Any]], deps: TriageDeps, sleep_s: float) -> list[CaseOutcome]:
    outcomes: list[CaseOutcome] = []
    for index, case in enumerate(cases, start=1):
        result, record = triage_and_register(case["query"], deps, source=EVAL_SOURCE)
        outcome = _outcome(case, result, record)
        outcomes.append(outcome)
        _progress(index, len(cases), outcome)
        if result.attempts > 0 and index < len(cases):
            time.sleep(sleep_s)
    return outcomes


def result_base(
    started: datetime, provider: str, model: str, prompt_version: str, guardrails: bool, dataset: Path
) -> str:
    model_slug = re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")
    dataset_tag = "" if dataset == DATASET_FILE else f"_{dataset.stem}"
    guardrails_tag = "" if guardrails else "_sin-guardrails"
    return f"{started:%Y%m%d-%H%M}_{provider}_{model_slug}_{prompt_version}{dataset_tag}{guardrails_tag}"


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def _outcome(case: dict[str, Any], result: TriageResult, record: dict[str, Any] | None) -> CaseOutcome:
    response = result.response
    return CaseOutcome(
        id=case["id"],
        query=case["query"],
        answer=response.answer,
        expected=case["expected_category"],
        predicted=response.category,
        confidence=response.confidence,
        actions=list(response.actions),
        fallback=result.fallback,
        attempts=result.attempts,
        invalid_responses=result.invalid_responses,
        latency_s=result.latency_s,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        cost_usd=record["cost_usd"] if record else None,
        cost_usd_list_price=record["cost_usd_list_price"] if record else None,
        guardrail=result.guardrail,
        cached=result.cached,
    )


def _progress(index: int, total: int, outcome: CaseOutcome) -> None:
    status = "ok" if outcome.correct else "FALLA"
    origin = " (respaldo)" if outcome.fallback else ""
    print(
        f"[{index:02d}/{total}] {outcome.id} esperada={outcome.expected} predicha={outcome.predicted} "
        f"{status}{origin} {outcome.latency_s:.1f} s",
        file=sys.stderr,
    )


def _sleep_s(provider: str, override: float | None) -> float:
    if override is not None:
        return override
    return load_models_config()["providers"][provider]["eval_sleep_s"]


def _require_free_model(provider: str, model: str) -> None:
    if provider == "openrouter" and not model.endswith(FREE_MODEL_SUFFIX):
        raise EvalError(f"{model} no es gratis; en OpenRouter la suite solo corre modelos que terminan en ':free'")


if __name__ == "__main__":
    sys.exit(main())
