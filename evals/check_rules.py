import json
import sys
from pathlib import Path
from typing import Any

from src.config import load_models_config
from src.guardrails import Guardrails
from src.policy import find_promises
from src.prompts import load_prompt
from src.schema import SupportResponse

CASES_FILE = Path(__file__).resolve().parent / "rule_cases.jsonl"
PROMISE_KIND = "promise"
INPUT_KIND = "input"
OUTPUT_KIND = "output"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    settings = load_models_config()["guardrails"]
    guardrails = Guardrails(canary=settings["canary"], max_query_chars=settings["max_query_chars"])
    system = load_prompt("v3").system
    cases = _load_cases(CASES_FILE)
    failed = 0
    for case in cases:
        passed, observed = _check(case, guardrails, system)
        failed += not passed
        print(f"{'✓' if passed else '✗'} [{case['kind']}] {case['note']} (espera {case['expect']}; {observed})")
    print(f"{len(cases) - failed} de {len(cases)} casos pasan")
    return 1 if failed else 0


def _load_cases(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _check(case: dict[str, Any], guardrails: Guardrails, system: str) -> tuple[bool, str]:
    kind, text, expect = case["kind"], case["text"], case["expect"]
    if kind == PROMISE_KIND:
        observed = "promesa" if find_promises(text) else "sin_promesa"
        return observed == expect, observed
    if kind == INPUT_KIND:
        screen = guardrails.screen_input(text)
        return _holds(expect, screen.blocked, screen.rules, screen.text), _describe(screen.blocked, screen.rules)
    if kind == OUTPUT_KIND:
        response = SupportResponse(answer=text, confidence=0.9, category="other", actions=["solicitar_mas_informacion"])
        screen = guardrails.screen_output(response, system)
        shown = screen.response.answer
        return _holds(expect, screen.blocked, screen.rules, shown), _describe(screen.blocked, screen.rules)
    raise ValueError(f"tipo de caso desconocido: {kind}")


def _holds(expect: str, blocked: bool, rules: tuple[str, ...], text: str) -> bool:
    if expect == "bloquea":
        return blocked
    if expect == "no_bloquea":
        return not blocked
    verb, _, arg = expect.partition(":")
    if verb == "regla":
        return arg in rules
    if verb == "sin_regla":
        return arg not in rules
    if verb == "texto":
        return arg in text
    if verb == "sin_texto":
        return arg not in text
    raise ValueError(f"expectativa desconocida: {expect}")


def _describe(blocked: bool, rules: tuple[str, ...]) -> str:
    return f"bloqueado={blocked}, reglas={list(rules)}"


if __name__ == "__main__":
    sys.exit(main())
