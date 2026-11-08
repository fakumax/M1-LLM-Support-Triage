import os

from src.config import load_models_config
from src.providers.base import LLMProvider, ProviderError, ProviderSettings
from src.providers.gemini import GeminiProvider
from src.providers.openrouter import OpenRouterProvider

PROVIDERS: dict[str, type[LLMProvider]] = {
    "openrouter": OpenRouterProvider,
    "gemini": GeminiProvider,
}


def get_provider(name: str, model: str | None = None) -> LLMProvider:
    if name not in PROVIDERS:
        raise ProviderError(f"proveedor desconocido: {name}")
    config = load_models_config()
    defaults = config["defaults"]
    provider_config = config["providers"][name]
    api_key_env = provider_config["api_key_env"]
    api_key = os.environ.get(api_key_env, "").strip()
    if not api_key:
        raise ProviderError(f"falta la variable {api_key_env} (completala en .env)")
    settings = ProviderSettings(
        api_key=api_key,
        model=model or provider_config["default_model"],
        base_url=provider_config.get("base_url"),
        temperature=defaults["temperature"],
        max_tokens=defaults["max_tokens"],
        timeout_s=defaults["timeout_s"],
        max_api_retries=defaults["max_api_retries"],
        max_retry_after_s=defaults["max_retry_after_s"],
    )
    return PROVIDERS[name](settings)
