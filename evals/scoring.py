from collections import Counter
from dataclasses import dataclass
from math import ceil, fsum
from typing import Any

from src.policy import find_promises
from src.schema import ACTION_CATALOG, CATEGORIES

CONFIDENCE_THRESHOLD = 0.8
PROJECTED_TICKETS_PER_DAY = 400


@dataclass(frozen=True)
class CaseOutcome:
    id: str
    query: str
    answer: str
    expected: str
    predicted: str
    confidence: float
    actions: list[str]
    fallback: bool
    attempts: int
    invalid_responses: int
    latency_s: float
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float | None
    cost_usd_list_price: float | None
    guardrail: tuple[str, ...] | None = None

    @property
    def correct(self) -> bool:
        return self.predicted == self.expected

    @property
    def actions_outside_catalog(self) -> list[str]:
        return [action for action in self.actions if action not in ACTION_CATALOG]

    @property
    def promises(self) -> list[str]:
        return find_promises(self.answer)


def summarize(outcomes: list[CaseOutcome]) -> dict[str, Any]:
    if not outcomes:
        raise ValueError("no hay casos para evaluar")
    per_category = class_scores(outcomes)
    correct = sum(outcome.correct for outcome in outcomes)
    return {
        "cases": len(outcomes),
        "correct": correct,
        "accuracy": correct / len(outcomes),
        "macro_f1": fsum(score["f1"] for score in per_category.values()) / len(per_category),
        "per_category": per_category,
        "confusion": confusion_matrix(outcomes),
        "contract": contract_stats(outcomes),
        "catalog": catalog_stats(outcomes),
        "calibration": calibration_stats(outcomes),
        "latency_s": latency_stats(outcomes),
        "tokens": token_stats(outcomes),
        "cost_usd": cost_stats(outcomes),
        "promises": promise_stats(outcomes),
        "guardrails": guardrail_stats(outcomes),
        "fallback_ids": [outcome.id for outcome in outcomes if outcome.fallback],
        "failed_ids": [outcome.id for outcome in outcomes if not outcome.correct],
    }


def class_scores(outcomes: list[CaseOutcome]) -> dict[str, dict[str, Any]]:
    scores: dict[str, dict[str, Any]] = {}
    for category in CATEGORIES:
        true_positive = sum(1 for o in outcomes if o.expected == category and o.predicted == category)
        predicted = sum(1 for o in outcomes if o.predicted == category)
        support = sum(1 for o in outcomes if o.expected == category)
        precision = _ratio(true_positive, predicted)
        recall = _ratio(true_positive, support)
        scores[category] = {
            "true_positive": true_positive,
            "predicted": predicted,
            "support": support,
            "precision": precision,
            "recall": recall,
            "f1": _ratio(2 * precision * recall, precision + recall),
        }
    return scores


def confusion_matrix(outcomes: list[CaseOutcome]) -> dict[str, dict[str, int]]:
    matrix = {expected: {predicted: 0 for predicted in CATEGORIES} for expected in CATEGORIES}
    for outcome in outcomes:
        matrix[outcome.expected][outcome.predicted] += 1
    return matrix


def contract_stats(outcomes: list[CaseOutcome]) -> dict[str, int]:
    return {
        "valid_first_try": sum(1 for o in outcomes if not o.fallback and o.invalid_responses == 0),
        "valid_after_retry": sum(1 for o in outcomes if not o.fallback and o.invalid_responses > 0),
        "fallback": sum(1 for o in outcomes if o.fallback),
    }


def catalog_stats(outcomes: list[CaseOutcome]) -> dict[str, Any]:
    answered = [o for o in outcomes if not o.fallback]
    actions = [action for o in answered for action in o.actions]
    outside = [action for action in actions if action not in ACTION_CATALOG]
    return {
        "answered_cases": len(answered),
        "actions": len(actions),
        "in_catalog": len(actions) - len(outside),
        "outside_catalog": dict(Counter(outside).most_common()),
        "cases_with_outside": [o.id for o in answered if o.actions_outside_catalog],
    }


def calibration_stats(outcomes: list[CaseOutcome]) -> dict[str, Any]:
    answered = [o for o in outcomes if not o.fallback]
    high = [o for o in answered if o.confidence >= CONFIDENCE_THRESHOLD]
    low = [o for o in answered if o.confidence < CONFIDENCE_THRESHOLD]
    return {"threshold": CONFIDENCE_THRESHOLD, "high": _bucket(high), "low": _bucket(low)}


def latency_stats(outcomes: list[CaseOutcome]) -> dict[str, float]:
    values = [o.latency_s for o in outcomes]
    return {
        "mean": fsum(values) / len(values),
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
    }


def token_stats(outcomes: list[CaseOutcome]) -> dict[str, int]:
    prompt = sum(o.prompt_tokens for o in outcomes)
    completion = sum(o.completion_tokens for o in outcomes)
    return {"prompt": prompt, "completion": completion, "total": prompt + completion}


def cost_stats(outcomes: list[CaseOutcome]) -> dict[str, Any]:
    real_total = _sum_optional([o.cost_usd for o in outcomes])
    list_total = _sum_optional([o.cost_usd_list_price for o in outcomes])
    real_per_ticket = None if real_total is None else real_total / len(outcomes)
    list_per_ticket = None if list_total is None else list_total / len(outcomes)
    return {
        "real_total": _round_usd(real_total),
        "list_total": _round_usd(list_total),
        "real_per_ticket": _round_usd(real_per_ticket),
        "list_per_ticket": _round_usd(list_per_ticket),
        "tickets_per_day": PROJECTED_TICKETS_PER_DAY,
        "real_per_day": _round_usd(_scale(real_per_ticket, PROJECTED_TICKETS_PER_DAY)),
        "list_per_day": _round_usd(_scale(list_per_ticket, PROJECTED_TICKETS_PER_DAY)),
    }


def promise_stats(outcomes: list[CaseOutcome]) -> dict[str, Any]:
    flagged = [outcome for outcome in outcomes if outcome.promises]
    return {
        "cases": len(flagged),
        "share": _ratio(len(flagged), len(outcomes)),
        "ids": [outcome.id for outcome in flagged],
    }


def guardrail_stats(outcomes: list[CaseOutcome]) -> dict[str, Any]:
    by_rule: dict[str, list[str]] = {}
    for outcome in outcomes:
        for code in outcome.guardrail or ():
            by_rule.setdefault(code, []).append(outcome.id)
    return {
        "cases": sum(1 for outcome in outcomes if outcome.guardrail),
        "by_rule": by_rule,
        "fallback_with_guardrail_ids": [o.id for o in outcomes if o.fallback and o.guardrail],
    }


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    rank = max(1, ceil(pct * len(ordered) / 100))
    return ordered[rank - 1]


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _bucket(outcomes: list[CaseOutcome]) -> dict[str, Any]:
    accuracy = None if not outcomes else sum(o.correct for o in outcomes) / len(outcomes)
    return {"cases": len(outcomes), "accuracy": accuracy}


def _sum_optional(values: list[float | None]) -> float | None:
    if any(value is None for value in values):
        return None
    return fsum(values)


def _scale(value: float | None, factor: float) -> float | None:
    return None if value is None else value * factor


def _round_usd(value: float | None) -> float | None:
    return None if value is None else round(value, 8)
