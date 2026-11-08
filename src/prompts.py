import json
from dataclasses import dataclass
from typing import Any

import yaml

from src.config import ROOT_DIR
from src.schema import ACTION_CATALOG

PROMPTS_DIR = ROOT_DIR / "prompts"


class PromptError(Exception):
    pass


@dataclass(frozen=True)
class Prompt:
    version: str
    technique: str
    system: str
    user_template: str
    examples: list[dict[str, Any]]


def load_prompt(version: str) -> Prompt:
    paths = sorted(PROMPTS_DIR.glob(f"{version}_*.yaml"))
    if not paths:
        raise PromptError(f"no existe el prompt {version} en prompts/")
    try:
        data = yaml.safe_load(paths[0].read_text(encoding="utf-8"))
        prompt = Prompt(
            version=data["version"],
            technique=data["technique"],
            system=data["system"],
            user_template=data["user_template"],
            examples=_examples(data.get("examples") or []),
        )
    except (OSError, KeyError, TypeError, yaml.YAMLError) as error:
        raise PromptError(f"prompt {version} mal formado") from error
    _check_catalog(prompt)
    return prompt


def _examples(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"ticket": item["ticket"], "output": item["output"]} for item in raw]


def _check_catalog(prompt: Prompt) -> None:
    missing = [action for action in ACTION_CATALOG if action not in prompt.system]
    if missing:
        raise PromptError(f"prompt {prompt.version} no menciona estas acciones del catálogo: {', '.join(missing)}")


def build_messages(prompt: Prompt, query: str) -> tuple[str, list[dict[str, str]]]:
    messages: list[dict[str, str]] = []
    for example in prompt.examples:
        messages.append({"role": "user", "content": _render(prompt, example["ticket"])})
        messages.append({"role": "assistant", "content": json.dumps(example["output"], ensure_ascii=False)})
    messages.append({"role": "user", "content": _render(prompt, query)})
    return prompt.system, messages


def _render(prompt: Prompt, ticket: str) -> str:
    return prompt.user_template.format(ticket=ticket).strip()
