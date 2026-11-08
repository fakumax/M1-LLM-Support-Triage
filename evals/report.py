import json
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from evals.scoring import CaseOutcome
from src.schema import CATEGORIES

QUERY_PREVIEW_CHARS = 90


@dataclass(frozen=True)
class RunInfo:
    timestamp: str
    provider: str
    model: str
    prompt_version: str
    dataset: str
    sleep_s: float
    guardrails: bool
    cache: bool


def build_payload(info: RunInfo, summary: dict[str, Any], outcomes: list[CaseOutcome]) -> dict[str, Any]:
    return {
        "run": asdict(info),
        "summary": summary,
        "cases": [_case_payload(outcome) for outcome in outcomes],
    }


def render_markdown(info: RunInfo, summary: dict[str, Any], outcomes: list[CaseOutcome]) -> str:
    blocks = [
        _title(info, summary),
        _global(summary),
        _per_category(summary),
        _confusion(summary),
        _contract(summary),
        _actions(info, summary),
        _calibration(summary),
        _operations(summary),
        _guardrails(info, summary),
        _failures(outcomes),
        _promises(outcomes),
    ]
    return "\n\n".join("\n".join(block) for block in blocks) + "\n"


def save_reports(directory: Path, base: str, payload: dict[str, Any], markdown: str) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{base}.json"
    md_path = directory / f"{base}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


def table(headers: Sequence[str], rows: Iterable[Sequence[object]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return lines


def pct(ratio: float) -> str:
    return f"{ratio * 100:.1f} %"


def pct_or_nd(ratio: float | None) -> str:
    return "n/d" if ratio is None else pct(ratio)


def usd(value: float | None) -> str:
    return "n/d" if value is None else f"{value:.6f}"


def latency_cell(latency: dict[str, float | None]) -> str:
    if latency["mean"] is None:
        return "n/d"
    return f"{latency['mean']:.2f} s / {latency['p50']:.2f} s / {latency['p95']:.2f} s"


def preview(text: str) -> str:
    flat = " ".join(text.split()).replace("|", "\\|")
    if len(flat) <= QUERY_PREVIEW_CHARS:
        return flat
    return flat[: QUERY_PREVIEW_CHARS - 1] + "…"


def _case_payload(outcome: CaseOutcome) -> dict[str, Any]:
    data = asdict(outcome)
    data["correct"] = outcome.correct
    data["actions_outside_catalog"] = outcome.actions_outside_catalog
    data["promises"] = outcome.promises
    return data


def _title(info: RunInfo, summary: dict[str, Any]) -> list[str]:
    return [
        f"# Evals: {info.provider} / {info.model} / prompt {info.prompt_version}",
        "",
        f"- Fecha: {info.timestamp}",
        f"- Dataset: `{info.dataset}` ({summary['cases']} casos)",
        f"- Pausa entre requests: {info.sleep_s} s",
        f"- Guardrails: {'activados' if info.guardrails else 'desactivados (--no-guardrails)'}",
        f"- Caché: {'activada (--cache)' if info.cache else 'desactivada'}",
    ]


def _global(summary: dict[str, Any]) -> list[str]:
    return [
        "## Resultado global",
        "",
        *table(
            ["Métrica", "Valor"],
            [
                ["Accuracy", f"{pct(summary['accuracy'])} ({summary['correct']} de {summary['cases']})"],
                ["Macro-F1", f"{summary['macro_f1']:.3f}"],
                ["Respaldos", summary["contract"]["fallback"]],
                [
                    "Respuestas con promesas indebidas",
                    f"{pct(summary['promises']['share'])} ({summary['promises']['cases']} de {summary['cases']})",
                ],
            ],
        ),
    ]


def _per_category(summary: dict[str, Any]) -> list[str]:
    rows = [
        [
            category,
            pct(score["precision"]),
            pct(score["recall"]),
            f"{score['f1']:.3f}",
            score["support"],
            score["predicted"],
            score["true_positive"],
        ]
        for category, score in summary["per_category"].items()
    ]
    return [
        "## Por categoría",
        "",
        *table(["Categoría", "Precision", "Recall", "F1", "Support", "Predichos", "Aciertos"], rows),
        "",
        "Precision = aciertos / predichos. Recall = aciertos / support.",
        "F1 = 2 x precision x recall / (precision + recall). Sin predicciones o sin casos, la métrica queda en 0.",
    ]


def _confusion(summary: dict[str, Any]) -> list[str]:
    matrix = summary["confusion"]
    column_totals = {category: 0 for category in CATEGORIES}
    rows: list[list[object]] = []
    for expected in CATEGORIES:
        row = matrix[expected]
        for predicted in CATEGORIES:
            column_totals[predicted] += row[predicted]
        rows.append([expected, *(row[predicted] for predicted in CATEGORIES), sum(row.values())])
    rows.append(["**Total**", *(column_totals[category] for category in CATEGORIES), sum(column_totals.values())])
    return [
        "## Matriz de confusión",
        "",
        "Filas: categoría esperada. Columnas: categoría predicha. Un respaldo cuenta como `other`.",
        "",
        *table(["esperada \\ predicha", *CATEGORIES, "Total"], rows),
    ]


def _contract(summary: dict[str, Any]) -> list[str]:
    contract = summary["contract"]
    cases = summary["cases"]
    return [
        "## Contrato",
        "",
        *table(
            ["Resultado", "Casos", "%"],
            [
                ["Válido al primer intento", contract["valid_first_try"], pct(contract["valid_first_try"] / cases)],
                [
                    "Válido tras reintento de validación",
                    contract["valid_after_retry"],
                    pct(contract["valid_after_retry"] / cases),
                ],
                ["Respaldo (contrato de fallback)", contract["fallback"], pct(contract["fallback"] / cases)],
            ],
        ),
        "",
        "Un reintento de validación ocurre cuando la respuesta no cumple el contrato y se pide corregirla.",
        "Un respaldo cuenta como `other`: si la esperada era `other`, suma como acierto. Por eso se informa aparte.",
    ]


def _actions(info: RunInfo, summary: dict[str, Any]) -> list[str]:
    catalog = summary["catalog"]
    lines = [
        "## Acciones",
        "",
        f"- Respuestas del modelo (sin respaldos): {catalog['answered_cases']} casos, {catalog['actions']} acciones.",
    ]
    if catalog["actions"]:
        share = catalog["in_catalog"] / catalog["actions"]
        lines.append(f"- Dentro del catálogo: {catalog['in_catalog']} de {catalog['actions']} ({pct(share)}).")
    if catalog["outside_catalog"]:
        items = ", ".join(f"`{name}` ({count})" for name, count in catalog["outside_catalog"].items())
        lines.append(f"- Fuera del catálogo: {items}.")
        lines.append(f"- Casos con acciones fuera del catálogo: {', '.join(catalog['cases_with_outside'])}.")
    else:
        lines.append("- Fuera del catálogo: ninguna.")
    return [*lines, "", _action_note(info)]


def _action_note(info: RunInfo) -> str:
    if info.guardrails:
        return (
            "Las acciones se miden en la respuesta final: con guardrails, las que están fuera del catálogo "
            "se descartan antes de medir, así que ese conteo queda en 0; con `--no-guardrails`, las del modelo."
        )
    return "Sin guardrails, las acciones se miden tal como las devuelve el modelo."


def _calibration(summary: dict[str, Any]) -> list[str]:
    calibration = summary["calibration"]
    threshold = calibration["threshold"]
    return [
        "## Confianza",
        "",
        *table(
            ["Confianza del modelo", "Casos", "Accuracy"],
            [
                [f">= {threshold}", calibration["high"]["cases"], pct_or_nd(calibration["high"]["accuracy"])],
                [f"< {threshold}", calibration["low"]["cases"], pct_or_nd(calibration["low"]["accuracy"])],
            ],
        ),
        "",
        "Calibración: con confianza alta, la accuracy tiene que ser mayor. Los respaldos no entran.",
    ]


def _operations(summary: dict[str, Any]) -> list[str]:
    latency = summary["latency_s"]
    tokens = summary["tokens"]
    cost = summary["cost_usd"]
    return [
        "## Operativas",
        "",
        *table(
            ["Métrica", "Valor"],
            [
                ["Latencia media / p50 / p95", latency_cell(latency)],
                [
                    "Tokens prompt / completion / total",
                    f"{tokens['prompt']} / {tokens['completion']} / {tokens['total']}",
                ],
                ["Casos servidos desde caché", f"{summary['cached_cases']} de {summary['cases']}"],
                ["Costo real total (USD)", usd(cost["real_total"])],
                ["Costo a precio de lista total (USD)", usd(cost["list_total"])],
                [
                    "Costo por ticket, real / lista (USD)",
                    f"{usd(cost['real_per_ticket'])} / {usd(cost['list_per_ticket'])}",
                ],
                [
                    f"Proyección a {cost['tickets_per_day']} tickets por día, real / lista (USD)",
                    f"{usd(cost['real_per_day'])} / {usd(cost['list_per_day'])}",
                ],
            ],
        ),
        "",
        "La latencia de cada caso incluye los reintentos de transporte y sus esperas, como en `triage()`.",
        "La latencia no cuenta los casos servidos desde caché; si son todos, queda en n/d.",
    ]


def _guardrails(info: RunInfo, summary: dict[str, Any]) -> list[str]:
    lines = ["## Guardrails", ""]
    if not info.guardrails:
        return lines + ["Desactivados (`--no-guardrails`): ninguna regla corrió."]
    stats = summary["guardrails"]
    if not stats["cases"]:
        return lines + ["Ninguna regla se activó.", "", _promise_note()]
    fallback_ids = stats["fallback_with_guardrail_ids"]
    fallback_note = f" ({', '.join(fallback_ids)})" if fallback_ids else ""
    return [
        *lines,
        *table(
            ["Regla", "Casos", "IDs"],
            [[f"`{code}`", len(ids), ", ".join(ids)] for code, ids in stats["by_rule"].items()],
        ),
        "",
        f"- Casos con alguna regla: {stats['cases']} de {summary['cases']}.",
        f"- Respaldos con guardrail activo: {len(fallback_ids)}{fallback_note}.",
        "",
        _promise_note(),
    ]


def _promise_note() -> str:
    return (
        "Las métricas de promesas miden la respuesta final: con guardrails, después del reemplazo; "
        "con `--no-guardrails`, la del modelo."
    )


def _failures(outcomes: list[CaseOutcome]) -> list[str]:
    failed = [outcome for outcome in outcomes if not outcome.correct]
    lines = [f"## Casos fallados ({len(failed)})", ""]
    if not failed:
        return lines + ["Ninguno."]
    rows = [
        [
            outcome.id,
            outcome.expected,
            outcome.predicted,
            f"{outcome.confidence:.2f}",
            "sí" if outcome.fallback else "no",
            preview(outcome.query),
        ]
        for outcome in failed
    ]
    return [*lines, *table(["id", "esperada", "predicha", "confianza", "respaldo", "query"], rows)]


def _promises(outcomes: list[CaseOutcome]) -> list[str]:
    flagged = [outcome for outcome in outcomes if outcome.promises]
    lines = [f"## Promesas indebidas ({len(flagged)})", ""]
    if not flagged:
        return lines + ["Ninguna."]
    rows = [[outcome.id, " / ".join(preview(fragment) for fragment in outcome.promises)] for outcome in flagged]
    return [*lines, *table(["id", "fragmentos detectados"], rows)]
