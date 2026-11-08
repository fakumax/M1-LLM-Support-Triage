import json
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
        _actions(summary),
        _calibration(summary),
        _operations(summary),
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
    ]


def _global(summary: dict[str, Any]) -> list[str]:
    return [
        "## Resultado global",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Accuracy | {_pct(summary['accuracy'])} ({summary['correct']} de {summary['cases']}) |",
        f"| Macro-F1 | {summary['macro_f1']:.3f} |",
        f"| Respaldos | {summary['contract']['fallback']} |",
        f"| Respuestas con promesas indebidas | {_pct(summary['promises']['share'])} "
        f"({summary['promises']['cases']} de {summary['cases']}) |",
    ]


def _per_category(summary: dict[str, Any]) -> list[str]:
    lines = [
        "## Por categoría",
        "",
        "| Categoría | Precision | Recall | F1 | Support | Predichos | Aciertos |",
        "|---|---|---|---|---|---|---|",
    ]
    for category, score in summary["per_category"].items():
        lines.append(
            f"| {category} | {_pct(score['precision'])} | {_pct(score['recall'])} | {score['f1']:.3f} "
            f"| {score['support']} | {score['predicted']} | {score['true_positive']} |"
        )
    lines += [
        "",
        "Precision = aciertos / predichos. Recall = aciertos / support.",
        "F1 = 2 x precision x recall / (precision + recall). Sin predicciones o sin casos, la métrica queda en 0.",
    ]
    return lines


def _confusion(summary: dict[str, Any]) -> list[str]:
    matrix = summary["confusion"]
    lines = [
        "## Matriz de confusión",
        "",
        "Filas: categoría esperada. Columnas: categoría predicha. Un respaldo cuenta como `other`.",
        "",
        "| esperada \\ predicha | " + " | ".join(CATEGORIES) + " | Total |",
        "|---" * (len(CATEGORIES) + 2) + "|",
    ]
    column_totals = {category: 0 for category in CATEGORIES}
    for expected in CATEGORIES:
        row = matrix[expected]
        for predicted in CATEGORIES:
            column_totals[predicted] += row[predicted]
        cells = " | ".join(str(row[predicted]) for predicted in CATEGORIES)
        lines.append(f"| {expected} | {cells} | {sum(row.values())} |")
    cells = " | ".join(str(column_totals[category]) for category in CATEGORIES)
    lines.append(f"| **Total** | {cells} | {sum(column_totals.values())} |")
    return lines


def _contract(summary: dict[str, Any]) -> list[str]:
    contract = summary["contract"]
    cases = summary["cases"]
    return [
        "## Contrato",
        "",
        "| Resultado | Casos | % |",
        "|---|---|---|",
        f"| Válido al primer intento | {contract['valid_first_try']} | {_pct(contract['valid_first_try'] / cases)} |",
        f"| Válido tras reintento de validación | {contract['valid_after_retry']} | "
        f"{_pct(contract['valid_after_retry'] / cases)} |",
        f"| Respaldo (contrato de fallback) | {contract['fallback']} | {_pct(contract['fallback'] / cases)} |",
        "",
        "Un reintento de validación ocurre cuando la respuesta no cumple el contrato y se pide corregirla.",
        "Un respaldo cuenta como `other`: si la esperada era `other`, suma como acierto. Por eso se informa aparte.",
    ]


def _actions(summary: dict[str, Any]) -> list[str]:
    catalog = summary["catalog"]
    lines = [
        "## Acciones",
        "",
        f"- Respuestas del modelo (sin respaldos): {catalog['answered_cases']} casos, {catalog['actions']} acciones.",
    ]
    if catalog["actions"]:
        share = catalog["in_catalog"] / catalog["actions"]
        lines.append(f"- Dentro del catálogo: {catalog['in_catalog']} de {catalog['actions']} ({_pct(share)}).")
    if catalog["outside_catalog"]:
        items = ", ".join(f"`{name}` ({count})" for name, count in catalog["outside_catalog"].items())
        lines.append(f"- Fuera del catálogo: {items}.")
        lines.append(f"- Casos con acciones fuera del catálogo: {', '.join(catalog['cases_with_outside'])}.")
    else:
        lines.append("- Fuera del catálogo: ninguna.")
    return lines


def _calibration(summary: dict[str, Any]) -> list[str]:
    calibration = summary["calibration"]
    threshold = calibration["threshold"]
    return [
        "## Confianza",
        "",
        "| Confianza del modelo | Casos | Accuracy |",
        "|---|---|---|",
        f"| >= {threshold} | {calibration['high']['cases']} | {_pct_or_nd(calibration['high']['accuracy'])} |",
        f"| < {threshold} | {calibration['low']['cases']} | {_pct_or_nd(calibration['low']['accuracy'])} |",
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
        "| Métrica | Valor |",
        "|---|---|",
        f"| Latencia media / p50 / p95 | {latency['mean']:.2f} s / {latency['p50']:.2f} s / {latency['p95']:.2f} s |",
        f"| Tokens prompt / completion / total | {tokens['prompt']} / {tokens['completion']} / {tokens['total']} |",
        f"| Costo real total (USD) | {_usd(cost['real_total'])} |",
        f"| Costo a precio de lista total (USD) | {_usd(cost['list_total'])} |",
        f"| Costo por ticket, real / lista (USD) | {_usd(cost['real_per_ticket'])} / {_usd(cost['list_per_ticket'])} |",
        f"| Proyección a {cost['tickets_per_day']} tickets por día, real / lista (USD) | "
        f"{_usd(cost['real_per_day'])} / {_usd(cost['list_per_day'])} |",
        "",
        "La latencia de cada caso incluye los reintentos de transporte y sus esperas, como en `triage()`.",
    ]


def _failures(outcomes: list[CaseOutcome]) -> list[str]:
    failed = [outcome for outcome in outcomes if not outcome.correct]
    lines = [f"## Casos fallados ({len(failed)})", ""]
    if not failed:
        return lines + ["Ninguno."]
    lines += [
        "| id | esperada | predicha | confianza | respaldo | query |",
        "|---|---|---|---|---|---|",
    ]
    for outcome in failed:
        origin = "sí" if outcome.fallback else "no"
        lines.append(
            f"| {outcome.id} | {outcome.expected} | {outcome.predicted} | {outcome.confidence:.2f} "
            f"| {origin} | {_preview(outcome.query)} |"
        )
    return lines


def _promises(outcomes: list[CaseOutcome]) -> list[str]:
    flagged = [outcome for outcome in outcomes if outcome.promises]
    lines = [f"## Promesas indebidas ({len(flagged)})", ""]
    if not flagged:
        return lines + ["Ninguna."]
    lines += [
        "| id | fragmentos detectados |",
        "|---|---|",
    ]
    for outcome in flagged:
        fragments = " / ".join(_preview(fragment) for fragment in outcome.promises)
        lines.append(f"| {outcome.id} | {fragments} |")
    return lines


def _preview(text: str) -> str:
    flat = " ".join(text.split()).replace("|", "\\|")
    if len(flat) <= QUERY_PREVIEW_CHARS:
        return flat
    return flat[: QUERY_PREVIEW_CHARS - 1] + "…"


def _pct(ratio: float) -> str:
    return f"{ratio * 100:.1f} %"


def _pct_or_nd(ratio: float | None) -> str:
    return "n/d" if ratio is None else _pct(ratio)


def _usd(value: float | None) -> str:
    return "n/d" if value is None else f"{value:.6f}"
