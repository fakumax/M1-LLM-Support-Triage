import argparse
import json
import re
import sys
import time
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from evals.report import (
    AdversarialRunInfo,
    AttackRun,
    RunInfo,
    build_adversarial_payload,
    build_payload,
    render_adversarial_markdown,
    render_markdown,
    save_reports,
)
from evals.scoring import (
    AttackOutcome,
    CaseOutcome,
    attack_layer,
    attack_succeeded,
    summarize,
    summarize_attacks,
    validate_success_if,
)
from src.config import ROOT_DIR, load_env, load_models_config
from src.pipeline import TriageDeps, build_triage_deps, triage_and_register
from src.prompts import PromptError
from src.providers import PROVIDERS
from src.providers.base import ProviderError
from src.schema import CATEGORIES
from src.triage import TriageError, TriageResult

DATASET_FILE = ROOT_DIR / "evals" / "dataset.jsonl"
ADVERSARIAL_FILE = ROOT_DIR / "evals" / "adversarial.jsonl"
RESULTS_DIR = ROOT_DIR / "evals" / "results"
DATASET_SUITE = "dataset"
ADVERSARIAL_SUITE = "adversarial"
EVAL_SOURCE = "eval"
ADVERSARIAL_SOURCE = "adversarial"
FREE_MODEL_SUFFIX = ":free"
DATASET_FIELDS = ("id", "query", "expected_category")
ATTACK_FIELDS = ("id", "attack", "variant", "type", "query", "success_if")


class EvalError(Exception):
    pass


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
    _require_free_model(deps.provider.name, deps.provider.model)
    sleep_s = _sleep_s(deps.provider.name, args.sleep)
    dataset = (args.dataset or DATASET_FILE).resolve()
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


def run_adversarial(args: argparse.Namespace, started: datetime) -> int:
    dataset = (args.dataset or ADVERSARIAL_FILE).resolve()
    cases = load_attacks(dataset)[: args.limit]
    deps_by_mode = [
        build_triage_deps(args.provider, args.model, args.prompt, with_guardrails=with_guardrails)
        for with_guardrails in (True, False)
    ]
    first = deps_by_mode[0]
    _require_free_model(first.provider.name, first.provider.model)
    sleep_s = _sleep_s(first.provider.name, args.sleep)
    base = result_base(started, first.provider.name, first.provider.model, first.prompt.version, True, dataset)
    if args.limit is None and (RESULTS_DIR / f"{base}.json").exists():
        raise EvalError(f"ya existe el reporte {base}.json; esperá un minuto y volvé a correr")
    canary = load_models_config()["guardrails"]["canary"]
    runs: list[AttackRun] = []
    for deps in deps_by_mode:
        print(f"Modo {'con' if deps.guardrails else 'sin'} guardrails:", file=sys.stderr)
        outcomes = run_attacks(cases, deps, sleep_s, canary)
        runs.append(
            AttackRun(guardrails=deps.guardrails is not None, summary=summarize_attacks(outcomes), outcomes=outcomes)
        )
    info = AdversarialRunInfo(
        timestamp=started.isoformat(timespec="seconds"),
        provider=first.provider.name,
        model=first.provider.model,
        prompt_version=first.prompt.version,
        dataset=_display_path(dataset),
        sleep_s=sleep_s,
    )
    markdown = render_adversarial_markdown(info, runs)
    print(markdown.rstrip())
    if args.limit is not None:
        print("Corrida parcial (--limit): no se guardaron reportes en evals/results/.", file=sys.stderr)
        return 0
    json_path, md_path = save_reports(RESULTS_DIR, base, build_adversarial_payload(info, runs), markdown)
    print(f"Reportes guardados: {json_path} y {md_path}", file=sys.stderr)
    return 0


def load_dataset(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for number, case in read_cases(path, DATASET_FIELDS):
        if case["expected_category"] not in CATEGORIES:
            raise EvalError(f"{path.name} línea {number}: categoría esperada inválida ({case['expected_category']})")
        cases.append(case)
    return cases


def load_attacks(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for number, case in read_cases(path, ATTACK_FIELDS):
        try:
            validate_success_if(case["success_if"])
        except ValueError as error:
            raise EvalError(f"{path.name} línea {number}: {error}") from error
        cases.append(case)
    return cases


def read_cases(path: Path, required: tuple[str, ...]) -> list[tuple[int, dict[str, Any]]]:
    if not path.is_file():
        raise EvalError(f"no existe el dataset {_display_path(path)}")
    cases: list[tuple[int, dict[str, Any]]] = []
    with path.open(encoding="utf-8") as file:
        for number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as error:
                raise EvalError(f"{path.name} línea {number} no es JSON válido") from error
            missing = [key for key in required if key not in case]
            if missing:
                raise EvalError(f"{path.name} línea {number} le faltan campos: {', '.join(missing)}")
            cases.append((number, case))
    if not cases:
        raise EvalError(f"{path.name} no tiene casos")
    return cases


def iter_runs(
    cases: list[dict[str, Any]], deps: TriageDeps, sleep_s: float, source: str
) -> Iterator[tuple[dict[str, Any], TriageResult, dict[str, Any] | None]]:
    for index, case in enumerate(cases, start=1):
        result, record = triage_and_register(case["query"], deps, source=source)
        yield case, result, record
        if result.attempts > 0 and index < len(cases):
            time.sleep(sleep_s)


def run_cases(cases: list[dict[str, Any]], deps: TriageDeps, sleep_s: float) -> list[CaseOutcome]:
    outcomes: list[CaseOutcome] = []
    for index, (case, result, record) in enumerate(iter_runs(cases, deps, sleep_s, EVAL_SOURCE), start=1):
        outcome = _outcome(case, result, record)
        outcomes.append(outcome)
        _progress(index, len(cases), outcome)
    return outcomes


def run_attacks(
    cases: list[dict[str, Any]], deps: TriageDeps, sleep_s: float, canary: str
) -> list[AttackOutcome]:
    outcomes: list[AttackOutcome] = []
    for index, (case, result, record) in enumerate(iter_runs(cases, deps, sleep_s, ADVERSARIAL_SOURCE), start=1):
        outcome = _attack_outcome(case, result, record, canary)
        outcomes.append(outcome)
        _attack_progress(index, len(cases), outcome)
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


def _attack_outcome(
    case: dict[str, Any], result: TriageResult, record: dict[str, Any] | None, canary: str
) -> AttackOutcome:
    response = result.response
    succeeded = attack_succeeded(case["success_if"], result, canary)
    return AttackOutcome(
        id=case["id"],
        attack=case["attack"],
        variant=case["variant"],
        type=case["type"],
        query=case["query"],
        answer=response.answer,
        category=response.category,
        confidence=response.confidence,
        actions=list(response.actions),
        succeeded=succeeded,
        layer=attack_layer(succeeded, result),
        fallback=result.fallback,
        attempts=result.attempts,
        latency_s=result.latency_s,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        cost_usd=record["cost_usd"] if record else None,
        cost_usd_list_price=record["cost_usd_list_price"] if record else None,
        guardrail=result.guardrail,
    )


def _progress(index: int, total: int, outcome: CaseOutcome) -> None:
    status = "ok" if outcome.correct else "FALLA"
    origin = " (respaldo)" if outcome.fallback else ""
    print(
        f"[{index:02d}/{total}] {outcome.id} esperada={outcome.expected} predicha={outcome.predicted} "
        f"{status}{origin} {outcome.latency_s:.1f} s",
        file=sys.stderr,
    )


def _attack_progress(index: int, total: int, outcome: AttackOutcome) -> None:
    status = "exitoso" if outcome.succeeded else "frenado"
    print(
        f"[{index:02d}/{total}] {outcome.id} {outcome.type} {status} ({outcome.layer}) {outcome.latency_s:.1f} s",
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
