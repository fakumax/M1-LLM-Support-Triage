import json
import re
import sys
import time
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from evals.report import save_reports
from src.config import ROOT_DIR, load_models_config
from src.pipeline import TriageDeps, triage_and_register
from src.triage import TriageResult

DATASET_FILE = ROOT_DIR / "evals" / "dataset.jsonl"
RESULTS_DIR = ROOT_DIR / "evals" / "results"
FREE_MODEL_SUFFIX = ":free"


class EvalError(Exception):
    pass


def read_cases(path: Path, required: tuple[str, ...]) -> list[tuple[int, dict[str, Any]]]:
    if not path.is_file():
        raise EvalError(f"no existe el dataset {display_path(path)}")
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


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return str(path)


def resolve_sleep(provider: str, override: float | None) -> float:
    if override is not None:
        return override
    return load_models_config()["providers"][provider]["eval_sleep_s"]


def require_free_model(provider: str, model: str) -> None:
    if provider == "openrouter" and not model.endswith(FREE_MODEL_SUFFIX):
        raise EvalError(f"{model} no es gratis; en OpenRouter la suite solo corre modelos que terminan en ':free'")


def result_base(
    started: datetime,
    provider: str,
    model: str,
    prompt_version: str,
    guardrails: bool,
    dataset: Path,
    cache: bool = False,
) -> str:
    model_slug = re.sub(r"[^a-z0-9]+", "-", model.lower()).strip("-")
    dataset_tag = "" if dataset == DATASET_FILE else f"_{dataset.stem}"
    cache_tag = "_cache" if cache else ""
    guardrails_tag = "" if guardrails else "_sin-guardrails"
    return (
        f"{started:%Y%m%d-%H%M}_{provider}_{model_slug}_{prompt_version}{dataset_tag}{cache_tag}{guardrails_tag}"
    )


def iter_runs(
    cases: list[dict[str, Any]], deps: TriageDeps, sleep_s: float, source: str
) -> Iterator[tuple[dict[str, Any], TriageResult, dict[str, Any]]]:
    for index, case in enumerate(cases, start=1):
        result, record = triage_and_register(case["query"], deps, source=source)
        yield case, result, record
        if result.attempts > 0 and index < len(cases):
            time.sleep(sleep_s)


def finish(markdown: str, base: str, payload: dict[str, Any], partial: bool) -> int:
    print(markdown.rstrip())
    if partial:
        print("Corrida parcial (--limit): no se guardaron reportes en evals/results/.", file=sys.stderr)
        return 0
    json_path, md_path = save_reports(RESULTS_DIR, base, payload, markdown)
    print(f"Reportes guardados: {json_path} y {md_path}", file=sys.stderr)
    return 0
