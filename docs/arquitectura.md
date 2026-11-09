# Arquitectura

Cómo está armado el código, qué hace cada módulo y cómo se extiende. El flujo general y el resumen de SOLID están en el [README](../README.md).

## Módulos

| Módulo | Responsabilidad |
|---|---|
| `src/main.py` | CLI: parsea argumentos, llama al pipeline, imprime el JSON o el error. |
| `src/pipeline.py` | Arma las dependencias y registra cada request. Lo usan la CLI y el runner de evals. |
| `src/triage.py` | Orquesta el flujo: guardrails, validación con reintento, respaldo, tokens y latencia sumados. |
| `src/schema.py` | Contrato `SupportResponse`, `ACTION_CATALOG` y `CATEGORIES`. |
| `src/parsing.py` | Extrae el primer objeto JSON de la respuesta y lo valida. |
| `src/prompts.py` | Carga `prompts/*.yaml` y arma el system prompt y los mensajes. |
| `src/guardrails.py` | Guardrails de entrada (reglas de riesgo, neutralización, enmascarado) y de salida. |
| `src/policy.py` | Detecta promesas indebidas (reintegros, descuentos, plazos) en español, portugués e inglés. |
| `src/cache.py` | `CachedProvider`, decorador de `LLMProvider` con caché MD5 en `data/cache/`. |
| `src/metrics.py` | Costo (fórmula y precios de `config/models.yaml`) y registro en `data/metrics.jsonl`. |
| `src/config.py` | Carga `.env` y `config/models.yaml`. |
| `src/providers/` | `base.py` (interfaz, excepciones, backoff), `openrouter.py`, `gemini.py` y el registro `PROVIDERS`. |
| `evals/runner.py` | Corre el dataset o la suite adversarial, registra las métricas y guarda los reportes. |
| `evals/scoring.py` | Métricas en funciones puras, sin I/O. Decide si un ataque tuvo éxito y en qué capa se frenó. |
| `evals/report.py` | Arma el `.json` y el `.md` de cada corrida. |
| `evals/adversarial.py` | Suite adversarial: criterios de éxito, capa que frenó cada ataque y reporte propio. |
| `evals/check_rules.py` | Corre `evals/rule_cases.jsonl` (116 casos) sin llamar a la API. Sale con código 1 si alguno falla. |
| `evals/common.py` | Helpers compartidos por el runner y la suite adversarial. |

## Árbol de carpetas

```text
config/models.yaml   defaults, proveedores, modelos, precios, pausas del runner y canary
prompts/             v1_zero_shot, v2_few_shot y v3_few_shot_reglas (YAML versionados)
evals/               dataset.jsonl, holdout.jsonl, adversarial.jsonl, rule_cases.jsonl, criterios_etiquetado.md, results/
data/                metrics.jsonl (versionado) y cache/ (ignorada por Git)
docs/                documentación de detalle
```

## SOLID

Dónde se ve SOLID:

- **S**: `main.py` solo parsea e imprime, `triage.py` orquesta y `scoring.py` calcula sin tocar el disco. Cada módulo tiene una responsabilidad.
- **O**: sumar un proveedor es una clase y una línea en `PROVIDERS`. Una regla de guardrail es una fila en `INPUT_RULES`. Una versión de prompt es un YAML nuevo.
- **L**: todos los proveedores devuelven `LLMResponse` y lanzan solo `ProviderError` o `TransientProviderError`. `CachedProvider` se comporta como el proveedor que envuelve.
- **I**: `LLMProvider` expone solo `complete()` (más `name` y `model`). Los guardrails de entrada y de salida son métodos separados (`screen_input` y `screen_output`), cada uno con su tipo de resultado.
- **D**: `triage()` recibe el proveedor, el prompt y los guardrails ya construidos. La CLI y el runner los arman.

## Contrato

`actions` son strings `snake_case` del catálogo de `src/schema.py`, con 16 acciones como `verificar_cobro_duplicado`, `gestionar_reintegro`, `escalar_a_soporte_tecnico_n2` o `derivar_a_agente_humano`. El contrato acepta cualquier string; el guardrail de salida `action_off_catalog` descarta las que no están en el catálogo.

## Robustez y reintentos

`triage()` siempre devuelve un resultado, salvo un error que no es transitorio (clave inválida, error 400). Hay dos ciclos anidados: el de transporte, dentro de cada proveedor, y el de validación, dentro de `triage()`.

```text
triage(consulta, proveedor, prompt, max_parse_retries)
  |  intento de validación (hasta max_parse_retries + 1)
  v
proveedor.complete()        intento de transporte (hasta max_api_retries + 1)
  |                         429 / 5xx / timeout: espera 1, 2, 4 s o Retry-After (tope 30 s)
  |                         agotado -> TransientProviderError -> RESPALDO (fallback=true)
  v
parse_support_response(texto)
  |-- válido    -> resultado (fallback=false)
  '-- inválido  -> agrega la salida como "assistant" y el error como "user"; vuelve al intento de validación
agotados los intentos de validación -> RESPALDO
```

Los SDK no reintentan por su cuenta (`max_retries=0` en OpenRouter y `HttpRetryOptions(attempts=1)` en Gemini), así que el reintento lo controla el proyecto y se ve en `config/models.yaml`.

## Proveedores

| Proveedor | SDK | Modelo por defecto | Clave | Límites del nivel gratuito |
|---|---|---|---|---|
| `openrouter` | `openai` 3.46.0, con la `base_url` de OpenRouter | `nvidia/nemotron-3.5-super-vl:free` | `OPENROUTER_API_KEY` | 20 requests por minuto. Por día, 50 si la cuenta compró menos de USD 10 en créditos y 1.000 si compró USD 10 o más. Al excederse responde 429. Fuente: [docs de OpenRouter](https://openrouter.ai/docs/api/reference/limits), consultada el 08/11/2026. |
| `gemini` | `google-genai` 3.0.0 | `gemini-3.5-flash-lite` | `GEMINI_API_KEY` | Nivel gratuito de AI Studio. Los límites por minuto y por día del modelo **no están publicados** en la documentación consultada. |

Los dos proveedores están detrás de `LLMProvider.complete(...)`. OpenRouter es el principal porque da acceso a modelos gratuitos con un SDK compatible con OpenAI. Gemini es otra empresa con otro SDK, así que la abstracción se prueba de verdad. Gemini usa `gemini-3.5-flash-lite` porque respondió en 2 s con JSON válido; en una prueba previa (no versionada), `gemini-3.8-flash` tardó 182 s en el nivel gratuito.

Para sumar un proveedor: una clase que herede de `LLMProvider` y defina los atributos `name` y `model`, además de `complete()`; una entrada en `PROVIDERS` (`src/providers/__init__.py`) y su bloque en `config/models.yaml`. `triage.py` no cambia.

## Ejemplo con Gemini y v1

Mismo tipo de ticket con Gemini y el prompt v1 (`--provider gemini --prompt v1`):

```json
{
  "answer": "Hola. Comprendo tu situación con el cargo duplicado de este mes. Un agente humano va a revisar tu caso para verificar el pago y coordinar los pasos a seguir.",
  "confidence": 0.95,
  "category": "billing",
  "actions": [
    "verificar_cobro_duplicado",
    "gestionar_reintegro"
  ]
}
```

## Entorno y variables de entorno

- Los comandos del inicio rápido clonan el repositorio público (no requiere login), crean el entorno e instalan las dependencias.
- Si se prefiere activar el venv, `.venv\Scripts\Activate.ps1` funciona igual. Si PowerShell lo bloquea, correr una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- Los ejemplos son de PowerShell en Windows. En macOS o Linux: `source .venv/bin/activate` y `cp` en lugar de `copy`.
- Después abrir `.env` y completar las claves. OpenRouter da la clave en openrouter.ai, en la sección Keys. Gemini, en aistudio.google.com, con Get API key.
- `.env` está en `.gitignore` y nunca se versiona. Una variable de entorno ya definida gana sobre el archivo, así que se puede probar una clave sin tocar `.env`. Si un modelo `:free` deja de existir o cambia de ID, usar `--model <otro :free>` o `--provider gemini`.

## Caché

**Caché MD5.** `src/cache.py` agrega `CachedProvider`, un decorador de `LLMProvider`. La clave es el MD5 de un JSON canónico con proveedor, modelo, system, mensajes, JSON Schema, temperature y max_tokens. Un acierto no llama a la API: `attempts=0`, `cost_usd` en 0 y los tokens originales para auditar. Con `--cache`, la segunda corrida de un caso sale de `data/cache/` sin llamar a la API. Tras la revisión final, el costo de lista de un acierto sale de los tokens originales, y la latencia de las evals excluye los casos de caché. `data/cache/` está en `.gitignore`.
