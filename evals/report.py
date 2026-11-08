import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from evals.scoring import AttackOutcome, CaseOutcome
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
        _actions(summary),
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
        f"| Casos servidos desde caché | {summary['cached_cases']} de {summary['cases']} |",
        f"| Costo real total (USD) | {_usd(cost['real_total'])} |",
        f"| Costo a precio de lista total (USD) | {_usd(cost['list_total'])} |",
        f"| Costo por ticket, real / lista (USD) | {_usd(cost['real_per_ticket'])} / {_usd(cost['list_per_ticket'])} |",
        f"| Proyección a {cost['tickets_per_day']} tickets por día, real / lista (USD) | "
        f"{_usd(cost['real_per_day'])} / {_usd(cost['list_per_day'])} |",
        "",
        "La latencia de cada caso incluye los reintentos de transporte y sus esperas, como en `triage()`.",
    ]


def _guardrails(info: RunInfo, summary: dict[str, Any]) -> list[str]:
    lines = ["## Guardrails", ""]
    if not info.guardrails:
        return lines + ["Desactivados (`--no-guardrails`): ninguna regla corrió."]
    stats = summary["guardrails"]
    if not stats["cases"]:
        return lines + ["Ninguna regla se activó.", "", _promise_note()]
    lines += [
        "| Regla | Casos | IDs |",
        "|---|---|---|",
    ]
    for code, ids in stats["by_rule"].items():
        lines.append(f"| `{code}` | {len(ids)} | {', '.join(ids)} |")
    fallback_ids = stats["fallback_with_guardrail_ids"]
    fallback_note = f" ({', '.join(fallback_ids)})" if fallback_ids else ""
    lines += [
        "",
        f"- Casos con alguna regla: {stats['cases']} de {summary['cases']}.",
        f"- Respaldos con guardrail activo: {len(fallback_ids)}{fallback_note}.",
        "",
        _promise_note(),
    ]
    return lines


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


ATTACK_LAYERS = ("ninguna", "entrada (bloqueo)", "prompt (entrada sin bloqueo)", "salida", "contrato", "prompt")
ATTACK_LAYER_LEGEND = (
    "- `ninguna`: el ataque tuvo éxito; ninguna capa lo frenó.",
    "- `entrada (bloqueo)`: la entrada cortó la consulta por riesgo alto. El modelo no se llamó.",
    "- `prompt (entrada sin bloqueo)`: la entrada marcó o neutralizó algo sin bloquear, y el modelo se resistió.",
    "- `salida`: una regla de salida reemplazó o descartó la respuesta del modelo.",
    "- `contrato`: no hubo JSON válido tras los reintentos, o el proveedor falló; se devolvió el respaldo.",
    "- `prompt`: ninguna regla se activó y el modelo no obedeció.",
)


@dataclass(frozen=True)
class AdversarialRunInfo:
    timestamp: str
    provider: str
    model: str
    prompt_version: str
    dataset: str
    sleep_s: float


@dataclass(frozen=True)
class AttackRun:
    guardrails: bool
    summary: dict[str, Any]
    outcomes: list[AttackOutcome]


def build_adversarial_payload(info: AdversarialRunInfo, runs: list[AttackRun]) -> dict[str, Any]:
    return {
        "run": asdict(info),
        "modes": {
            _mode_key(run): {"summary": run.summary, "cases": [asdict(outcome) for outcome in run.outcomes]}
            for run in runs
        },
    }


def render_adversarial_markdown(info: AdversarialRunInfo, runs: list[AttackRun]) -> str:
    blocks = [
        _attack_title(info, runs),
        _attack_global(runs),
        _attack_by_type(runs),
        _attack_layers(runs),
        _attack_cases(runs),
        _attack_operations(runs),
        _attack_successes(runs),
    ]
    return "\n\n".join("\n".join(block) for block in blocks) + "\n"


def _mode_key(run: AttackRun) -> str:
    return "with_guardrails" if run.guardrails else "without_guardrails"


def _mode_label(run: AttackRun) -> str:
    return "Con guardrails" if run.guardrails else "Sin guardrails"


def _attack_title(info: AdversarialRunInfo, runs: list[AttackRun]) -> list[str]:
    attacks = len({outcome.attack for outcome in runs[0].outcomes})
    return [
        f"# Evals adversariales: {info.provider} / {info.model} / prompt {info.prompt_version}",
        "",
        f"- Fecha: {info.timestamp}",
        f"- Suite: `{info.dataset}` ({attacks} ataques, {runs[0].summary['cases']} casos: base y variante trivial)",
        f"- Pausa entre requests: {info.sleep_s} s",
        "- Modos: con guardrails y sin guardrails (`--no-guardrails`), mismo prompt, sin caché.",
    ]


def _attack_global(runs: list[AttackRun]) -> list[str]:
    lines = [
        "## Resultado global",
        "",
        "| Modo | Ataques exitosos | Tasa de éxito | Bloqueados | Tasa de bloqueo |",
        "|---|---|---|---|---|",
    ]
    for run in runs:
        summary = run.summary
        lines.append(
            f"| {_mode_label(run)} | {summary['succeeded']} de {summary['cases']} | {_pct(summary['success_rate'])} "
            f"| {summary['blocked']} de {summary['cases']} | {_pct(summary['block_rate'])} |"
        )
    lines += [
        "",
        "Éxito: la respuesta final que recibe el usuario cumple el criterio `success_if` del ataque.",
        "Bloqueado: la entrada cortó la consulta o la salida reemplazó la respuesta.",
    ]
    return lines


def _attack_by_type(runs: list[AttackRun]) -> list[str]:
    header = "| Tipo | Casos | " + " | ".join(f"Éxitos {_mode_label(run).lower()}" for run in runs) + " |"
    lines = ["## Por tipo", "", header, "|---|---|" + "---|" * len(runs)]
    for kind, base in runs[0].summary["by_type"].items():
        cells = [f"{run.summary['by_type'][kind]['succeeded']} de {base['cases']}" for run in runs]
        lines.append(f"| {kind} | {base['cases']} | " + " | ".join(cells) + " |")
    return lines


def _attack_layers(runs: list[AttackRun]) -> list[str]:
    header = "| Capa que frenó | " + " | ".join(_mode_label(run) for run in runs) + " |"
    lines = ["## Capa que frenó cada ataque", "", header, "|---|" + "---|" * len(runs)]
    for layer in ATTACK_LAYERS:
        counts = [run.summary["by_layer"].get(layer, 0) for run in runs]
        lines.append(f"| {layer} | " + " | ".join(str(count) for count in counts) + " |")
    return [*lines, "", *ATTACK_LAYER_LEGEND]


def _attack_cases(runs: list[AttackRun]) -> list[str]:
    rules = {outcome.id: outcome.guardrail for run in runs if run.guardrails for outcome in run.outcomes}
    header = "| id | tipo | consulta | " + " | ".join(_mode_label(run) for run in runs) + " | reglas (con guardrails) |"
    lines = ["## Casos", "", header, "|---|---|---|" + "---|" * len(runs) + "---|"]
    lookups = [{outcome.id: outcome for outcome in run.outcomes} for run in runs]
    for outcome in runs[0].outcomes:
        cells = [_attack_cell(lookup[outcome.id]) for lookup in lookups]
        fired = ", ".join(rules.get(outcome.id) or ()) or "-"
        lines.append(
            f"| {outcome.id} | {outcome.type} | {_preview(outcome.query)} | " + " | ".join(cells) + f" | {fired} |"
        )
    return lines


def _attack_cell(outcome: AttackOutcome) -> str:
    return "**éxito**" if outcome.succeeded else f"frenado: {outcome.layer}"


def _attack_operations(runs: list[AttackRun]) -> list[str]:
    lines = [
        "## Operativas",
        "",
        "| Modo | Latencia media / p50 / p95 | Tokens prompt / completion / total | "
        "Costo real total (USD) | Costo a precio de lista total (USD) |",
        "|---|---|---|---|---|",
    ]
    for run in runs:
        latency = run.summary["latency_s"]
        tokens = run.summary["tokens"]
        cost = run.summary["cost_usd"]
        lines.append(
            f"| {_mode_label(run)} | {latency['mean']:.2f} s / {latency['p50']:.2f} s / {latency['p95']:.2f} s "
            f"| {tokens['prompt']} / {tokens['completion']} / {tokens['total']} "
            f"| {_usd(cost['real_total'])} | {_usd(cost['list_total'])} |"
        )
    return [*lines, "", "Los bloqueos no llaman al modelo: no suman tokens ni costo."]


def _attack_successes(runs: list[AttackRun]) -> list[str]:
    lines = ["## Respuestas de los ataques exitosos", ""]
    found = [(run, outcome) for run in runs for outcome in run.outcomes if outcome.succeeded]
    if not found:
        return [*lines, "Ninguno."]
    for run, outcome in found:
        lines.append(f"- {_mode_label(run)}, `{outcome.id}` ({outcome.type}): {_preview(outcome.answer)}")
    return lines
