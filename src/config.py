from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"
MODELS_FILE = ROOT_DIR / "config" / "models.yaml"


def load_env() -> None:
    load_dotenv(ENV_FILE)


def load_models_config() -> dict[str, Any]:
    with MODELS_FILE.open(encoding="utf-8") as file:
        return yaml.safe_load(file)
