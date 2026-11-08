import argparse
import json
import sys

from src.config import load_env, load_models_config
from src.pipeline import build_triage_deps, triage_and_register
from src.prompts import PromptError
from src.providers import PROVIDERS
from src.providers.base import ProviderError
from src.triage import TriageError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    defaults = load_models_config()["defaults"]
    parser = argparse.ArgumentParser(description="Triage de tickets de soporte de Nubbix.")
    parser.add_argument("query", help="consulta del cliente en texto libre")
    parser.add_argument("--provider", default=defaults["provider"], choices=sorted(PROVIDERS))
    parser.add_argument("--model", help="ID del modelo (por defecto, el de config/models.yaml)")
    parser.add_argument("--prompt", default=defaults["prompt_version"], help="versión del prompt, por ejemplo v1")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    load_env()
    args = parse_args(argv)
    try:
        deps = build_triage_deps(args.provider, args.model, args.prompt)
        result, _ = triage_and_register(args.query, deps, source="cli")
    except (ProviderError, TriageError, PromptError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    if result.guardrail:
        print(f"Aviso: guardrails activados: {', '.join(result.guardrail)}", file=sys.stderr)
    if result.fallback:
        print("Aviso: no se pudo procesar automáticamente; la consulta queda para un agente humano.", file=sys.stderr)
    print(json.dumps(result.response.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
