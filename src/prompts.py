import json
from dataclasses import dataclass
from typing import Any

import yaml

from src.config import ROOT_DIR

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
    data = yaml.safe_load(paths[0].read_text(encoding="utf-8"))
    return Prompt(
        version=data["version"],
        technique=data["technique"],
        system=data["system"],
        user_template=data["user_template"],
        examples=data.get("examples") or [],
    )


def build_messages(prompt: Prompt, query: str) -> tuple[str, list[dict[str, str]]]:
    messages: list[dict[str, str]] = []
    for example in prompt.examples:
        messages.append({"role": "user", "content": _render(prompt, example["ticket"])})
        messages.append({"role": "assistant", "content": json.dumps(example["output"], ensure_ascii=False)})
    messages.append({"role": "user", "content": _render(prompt, query)})
    return prompt.system, messages


def _render(prompt: Prompt, ticket: str) -> str:
    return prompt.user_template.format(ticket=ticket).strip()
