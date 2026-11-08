import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from evals.adversarial import run_adversarial
from evals.common import (
    DATASET_FILE,
    RESULTS_DIR,
    EvalError,
    display_path,
    finish,
    iter_runs,
    read_cases,
    require_free_model,
    resolve_sleep,
    result_base,
)
from evals.report import RunInfo, build_payload, render_markdown
from evals.scoring import CaseOutcome, summarize
from src.config import load_env, load_models_config
from src.pipeline import TriageDeps, build_triage_deps
from src.prompts import PromptError
from src.providers import PROVIDERS
from src.providers.base import ProviderError
from src.schema import CATEGORIES
from src.triage import TriageError, TriageResult

DATASET_SUITE = "dataset"
ADVERSARIAL_SUITE = "adversarial"
EVAL_SOURCE = "eval"
DATASET_FIELDS = ("id", "query", "expected_category")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_models_config()["defaults"]
    parser = argparse.ArgumentParser(description="Corre la suite de evals y reporta métricas.")
    parser.add_argument(
        "--suite",
        default=DATASET_SUITE,
        choices=[DATASET_SUITE, ADVERSARIAL_SUITE],
        help="dataset: clasificación; adversarial: ataques con y sin guardrails",
    )
    parser.add_argument("--provider", default=defaults["provider"], choices=sorted(PROVIDERS))
    parser.add_argument("--model", help="ID del modelo (por defecto, el de config/models.yaml)")
    parser.add_argument("--prompt", default=defaults["prompt_version"], help="versión del prompt, por ejemplo v1")
    parser.add_argument("--dataset", type=Path, help="JSONL a evaluar (por defecto, el de --suite)")
    parser.add_argument("--limit", type=int, help="evalúa solo los primeros N casos; no guarda reportes")
    parser.add_argument("--sleep", type=float, help="segundos entre requests (por defecto, según el proveedor)")
    parser.add_argument("--no-guardrails", action="store_true", help="desactiva los guardrails de entrada y salida")
    parser.add_argument("--cache", action="store_true", help="reutiliza respuestas de data/cache/ sin llamar a la API")
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error("--limit tiene que ser al menos 1")
    if args.sleep is not None and args.sleep < 0:
        parser.error("--sleep no puede ser negativo")
    if args.suite == ADVERSARIAL_SUITE and args.no_guardrails:
        parser.error("la suite adversarial ya corre con y sin guardrails; no lleva --no-guardrails")
    if args.suite == ADVERSARIAL_SUITE and args.cache:
        parser.error("la suite adversarial no usa --cache: cada modo tiene que llamar al modelo")
    return args


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    load_env()
    args = parse_args(argv)
    started = datetime.now()
    try:
        if args.suite == ADVERSARIAL_SUITE:
            return run_adversarial(args, started)
        return run_dataset(args, started)
    except (ProviderError, TriageError, PromptError, EvalError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


def run_dataset(args: argparse.Namespace, started: datetime) -> int:
    deps = build_triage_deps(
        args.provider,
        args.model,
        args.prompt,
        with_guardrails=not args.no_guardrails,
        with_cache=args.cache,
    )
    require_free_model(deps.provider.name, deps.provider.model)
    sleep_s = resolve_sleep(deps.provider.name, args.sleep)
    dataset = (args.dataset or DATASET_FILE).resolve()
    cases = load_dataset(dataset)[: args.limit]
    base = result_base(
        started,
        deps.provider.name,
        deps.provider.model,
        deps.prompt.version,
        deps.guardrails is not None,
        dataset,
        cache=args.cache,
    )
    if args.limit is None and (RESULTS_DIR / f"{base}.json").exists():
        raise EvalError(f"ya existe el reporte {base}.json; esperá un minuto y volvé a correr")
    outcomes = run_cases(cases, deps, sleep_s)
    info = RunInfo(
        timestamp=started.isoformat(timespec="seconds"),
        provider=deps.provider.name,
        model=deps.provider.model,
        prompt_version=deps.prompt.version,
        dataset=display_path(dataset),
        sleep_s=sleep_s,
        guardrails=deps.guardrails is not None,
        cache=args.cache,
    )
    summary = summarize(outcomes)
    markdown = render_markdown(info, summary, outcomes)
    return finish(markdown, base, build_payload(info, summary, outcomes), partial=args.limit is not None)


def load_dataset(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for number, case in read_cases(path, DATASET_FIELDS):
        if case["expected_category"] not in CATEGORIES:
            raise EvalError(f"{path.name} línea {number}: categoría esperada inválida ({case['expected_category']})")
        cases.append(case)
    return cases


def run_cases(cases: list[dict[str, Any]], deps: TriageDeps, sleep_s: float) -> list[CaseOutcome]:
    outcomes: list[CaseOutcome] = []
    for index, (case, result, record) in enumerate(iter_runs(cases, deps, sleep_s, EVAL_SOURCE), start=1):
        outcome = _outcome(case, result, record)
        outcomes.append(outcome)
        _progress(index, len(cases), outcome)
    return outcomes


def _outcome(case: dict[str, Any], result: TriageResult, record: dict[str, Any]) -> CaseOutcome:
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
        cost_usd=record["cost_usd"],
        cost_usd_list_price=record["cost_usd_list_price"],
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


if __name__ == "__main__":
    sys.exit(main())
