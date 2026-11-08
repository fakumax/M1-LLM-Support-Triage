import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from src.config import ROOT_DIR
from src.providers.base import LLMProvider, LLMResponse

CACHE_DIR = ROOT_DIR / "data" / "cache"


def cache_key(
    provider: str,
    model: str,
    system: str,
    messages: list[dict[str, str]],
    json_schema: dict[str, Any],
    temperature: float,
    max_tokens: int,
) -> str:
    canonical = json.dumps(
        {
            "provider": provider,
            "model": model,
            "system": system,
            "messages": messages,
            "json_schema": json_schema,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.md5(canonical.encode("utf-8"), usedforsecurity=False).hexdigest()


class CachedProvider(LLMProvider):
    def __init__(self, inner: LLMProvider, temperature: float, max_tokens: int, directory: Path = CACHE_DIR) -> None:
        self._inner = inner
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._directory = directory
        self.name = inner.name
        self.model = inner.model

    def complete(self, system: str, messages: list[dict[str, str]], json_schema: dict[str, Any]) -> LLMResponse:
        key = cache_key(
            self.name, self.model, system, messages, json_schema, self._temperature, self._max_tokens
        )
        path = self._directory / f"{key}.json"
        hit = _load(path, self.name, self.model)
        if hit is not None:
            return hit
        response = self._inner.complete(system, messages, json_schema)
        if response.text.strip():
            _store(path, response)
        return response


def _load(path: Path, provider: str, model: str) -> LLMResponse | None:
    started = time.perf_counter()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        text, prompt_tokens, completion_tokens = data["text"], data["prompt_tokens"], data["completion_tokens"]
        if not text.strip():
            return None
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None
    return LLMResponse(
        text=text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_s=round(time.perf_counter() - started, 3),
        provider=provider,
        model=model,
        reported_cost_usd=data.get("reported_cost_usd"),
        attempts=0,
        cached=True,
    )


def _store(path: Path, response: LLMResponse) -> None:
    payload = {
        "text": response.text,
        "prompt_tokens": response.prompt_tokens,
        "completion_tokens": response.completion_tokens,
        "reported_cost_usd": response.reported_cost_usd,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except OSError as error:
        print(f"Aviso: no se pudo guardar la caché: {error}", file=sys.stderr)
