import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.config import ROOT_DIR, load_models_config
from src.triage import TriageResult

METRICS_FILE = ROOT_DIR / "data" / "metrics.jsonl"
TOKENS_PER_MTOK = 1_000_000


class MetricsError(Exception):
    pass


@dataclass(frozen=True)
class ListPrice:
    in_per_mtok: float
    out_per_mtok: float


@dataclass(frozen=True)
class ModelPricing:
    price_in_per_mtok: float
    price_out_per_mtok: float
    list_price: ListPrice


def estimate_cost(prompt_tokens: int, completion_tokens: int, in_per_mtok: float, out_per_mtok: float) -> float:
    cost = prompt_tokens * in_per_mtok / TOKENS_PER_MTOK + completion_tokens * out_per_mtok / TOKENS_PER_MTOK
    return round(cost, 8)


def find_pricing(provider: str, model: str) -> ModelPricing | None:
    models = load_models_config()["providers"].get(provider, {}).get("models", {})
    entry = models.get(model)
    if entry is None:
        return None
    try:
        list_price = entry["list_price"]
        return ModelPricing(
            price_in_per_mtok=float(entry["price_in_per_mtok"]),
            price_out_per_mtok=float(entry["price_out_per_mtok"]),
            list_price=ListPrice(
                in_per_mtok=float(list_price["in_per_mtok"]),
                out_per_mtok=float(list_price["out_per_mtok"]),
            ),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise MetricsError(f"precio mal configurado para {model} en config/models.yaml") from error


def build_record(result: TriageResult, source: str, prompt_version: str) -> dict[str, Any]:
    llm = result.llm
    pricing = find_pricing(llm.provider, llm.model)
    cost_usd = None
    cost_usd_list_price = None
    if pricing is not None:
        cost_usd = estimate_cost(
            llm.prompt_tokens, llm.completion_tokens, pricing.price_in_per_mtok, pricing.price_out_per_mtok
        )
        cost_usd_list_price = estimate_cost(
            llm.prompt_tokens,
            llm.completion_tokens,
            pricing.list_price.in_per_mtok,
            pricing.list_price.out_per_mtok,
        )
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": source,
        "provider": llm.provider,
        "model": llm.model,
        "prompt_version": prompt_version,
        "prompt_tokens": llm.prompt_tokens,
        "completion_tokens": llm.completion_tokens,
        "total_tokens": llm.prompt_tokens + llm.completion_tokens,
        "latency_s": result.latency_s,
        "cost_usd": cost_usd,
        "cost_usd_list_price": cost_usd_list_price,
        "reported_cost_usd": llm.reported_cost_usd,
        "attempts": result.attempts,
        "fallback": result.fallback,
        "category": result.response.category,
        "guardrail": result.guardrail,
    }


def append_metrics(record: dict[str, Any], path: Path) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError as error:
        raise MetricsError(f"no se pudo escribir {path}: {error}") from error
