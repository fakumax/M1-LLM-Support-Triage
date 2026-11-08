import argparse
import json
import sys

from src.config import load_env, load_models_config
from src.prompts import PromptError, load_prompt
from src.providers import PROVIDERS, get_provider
from src.providers.base import ProviderError
from src.triage import TriageError, triage


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
        provider = get_provider(args.provider, args.model)
        result = triage(args.query, provider, load_prompt(args.prompt))
    except (ProviderError, TriageError, PromptError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result.response.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
