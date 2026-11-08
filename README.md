# M1 · LLM Support Triage

Servicio de triage de tickets de soporte con LLMs: recibe una consulta en texto libre y devuelve una respuesta estructurada con el contrato `{answer, confidence, category, actions}`.

> Proyecto integrador del Módulo 1 de AI Engineering (Henry). Caso: **Nubbix**, un SaaS ficticio de gestión para pymes de LATAM cuya mesa de soporte recibe unos 400 tickets por día.

> 🚧 En desarrollo.

## Requisitos

- Python 3.12
- API key de [OpenRouter](https://openrouter.ai) y de Gemini ([Google AI Studio](https://aistudio.google.com)). Las dos tienen un nivel gratuito.

## Instalación

```bash
git clone https://github.com/fakumax/M1-LLM-Support-Triage.git
cd M1-LLM-Support-Triage
python -m venv .venv
```

Activar el entorno virtual:

- Windows: `.venv\Scripts\activate`
- macOS / Linux: `source .venv/bin/activate`

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

## Configuración

Copiar `.env.example` a `.env` y completar las claves:

| Variable | Descripción |
|---|---|
| `OPENROUTER_API_KEY` | API key de OpenRouter |
| `GEMINI_API_KEY` | API key de Gemini (Google AI Studio) |

`.env` está en `.gitignore`: las credenciales nunca se suben al repositorio.

## Uso

```powershell
python -m src.main "Buen día. El mes pasado me cobraron el plan dos veces en la misma tarjeta. ¿Me pueden devolver uno de los cargos?"
```

Salida de una ejecución real (proveedor y modelo por defecto, prompt `v1`):

```json
{
  "answer": "Buen día. Lamento los inconvenientes con el cobro duplicado. Un agente revisará si hubo un cargo duplicado en tu tarjeta y evaluará la posibilidad de un reintegro. Para agilizar, ¿podrías indicarme la fecha aproximada y el monto de los cargos?",
  "confidence": 0.95,
  "category": "billing",
  "actions": [
    "verificar_cobro_duplicado",
    "gestionar_reintegro"
  ]
}
```

Mismo ticket con Gemini (`--provider gemini`), salida real:

```powershell
python -m src.main "Hola, me cobraron dos veces la suscripción de este mes, necesito que me reintegren uno de los cargos." --provider gemini
```

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

El JSON sale solo por stdout. Los avisos y errores van a stderr:

- Error que impide responder (consulta vacía, clave faltante, error 400 o 401 del proveedor): `Error: ...` y código de salida 1.
- Error transitorio que no se resolvió con reintentos, o respuesta inválida agotada: se imprime el contrato de respaldo, avisa `Aviso: no se pudo procesar automáticamente...` y sale con código 0. La CLI no se cae por un error transitorio.

```
Error: la consulta está vacía
```

Opciones:

| Opción | Descripción | Por defecto |
|---|---|---|
| `--provider` | Proveedor LLM registrado en `src/providers/__init__.py`: `openrouter` o `gemini` | `openrouter` |
| `--model` | ID del modelo del proveedor | El `default_model` del proveedor en `config/models.yaml` |
| `--prompt` | Versión del prompt en `prompts/` | `v1` |

Con OpenRouter, la regla del proyecto es usar solo modelos `:free`. El código no lo fuerza: la key tiene tope de gasto de USD 0, así que un modelo pago falla con un error claro.

## Proveedores

Dos proveedores detrás de la misma interfaz `LLMProvider.complete(...)`. OpenRouter es el principal porque da acceso a modelos gratuitos con un SDK compatible con OpenAI. Gemini es el segundo porque es otra empresa, con otro SDK: así la abstracción se prueba de verdad.

| Proveedor | SDK | Modelo por defecto | Clave | Límites del nivel gratuito |
|---|---|---|---|---|
| `openrouter` | `openai` 3.46.0, con `base_url` de OpenRouter | `nvidia/nemotron-3.5-super-vl:free` | `OPENROUTER_API_KEY` | 20 requests por minuto. Por día: 50 si la cuenta compró menos de USD 10 en créditos, 1.000 si compró USD 10 o más. Al excederse responde 429. Fuente: https://openrouter.ai/docs/api/reference/limits (consultada el 08/11/2026). |
| `gemini` | `google-genai` 3.0.0 | `gemini-3.5-flash-lite` | `GEMINI_API_KEY` | Nivel gratuito de AI Studio. Los límites por minuto y por día del modelo **no están publicados** en la documentación pública consultada (las páginas del modelo y de límites no los muestran, y la página de límites de AI Studio pide iniciar sesión). **Pendiente de confirmar en la cuenta** antes de correr el dataset completo. |

Gemini se configura con `--provider gemini`. Su modelo por defecto es `gemini-3.5-flash-lite`: en la prueba de la Parte 4 respondió en 2 s con JSON válido. `gemini-3.8-flash` tardó 182 s en el nivel gratuito, así que no es el default.

Para sumar un proveedor: una clase que herede de `LLMProvider`, una entrada en `PROVIDERS` (`src/providers/__init__.py`) y su bloque en `config/models.yaml`. `triage.py` no cambia.

Parámetros por defecto (`config/models.yaml`):

| Parámetro | Valor | Por qué |
|---|---|---|
| `temperature` | 0 | Reduce la variación de la clasificación entre corridas del mismo ticket. |
| `max_tokens` | 2000 | Los modelos gratuitos razonan antes de responder (400 a 1.500 tokens); con menos, el JSON llega cortado. |
| `timeout_s` | 120 | Un ticket de la Parte 3 tardó 39,2 s; con 60 s no había margen. Se aplica a cada intento. |
| `max_api_retries` | 3 | Reintentos de transporte ante 429, 5xx y timeouts: esperas de 1, 2 y 4 s, o el `Retry-After` del servidor. |
| `max_retry_after_s` | 30 | Tope de la espera de `Retry-After`. Sin tope, un 429 con una espera larga deja la CLI colgada. |
| `max_parse_retries` | 2 | Reintentos cuando la respuesta no es un JSON válido del contrato (hasta 3 llamadas en total). |

## Robustez

`triage()` siempre devuelve un resultado, salvo un error que no es transitorio (clave inválida, error 400). Hay dos ciclos anidados: el de transporte, dentro de cada proveedor, y el de validación, dentro de `triage()`.

```text
triage(consulta, proveedor, prompt, max_parse_retries)
  |
  |  intento de validación  (hasta max_parse_retries + 1)
  v
+--------------------------------------------------------+
| proveedor.complete()                                   |
|   intento de transporte (hasta max_api_retries + 1)    |
|   429 / 5xx / timeout: espera 1, 2, 4 s o Retry-After  |
|   (tope max_retry_after_s); agotado -> transitorio     |
+--------------------------------------------------------+
  |                         |
  | respuesta               | TransientProviderError agotado
  v                         v
parse_support_response()   RESPALDO (fallback=true)
  |          |
  | válida   | inválida: se agrega la salida como "assistant"
  v          |          y el error de validación como "user";
RESULTADO    |          vuelve al intento de validación
(fallback=false)
                    se agotaron los intentos de validación -> RESPALDO
```

El contrato de respaldo es fijo: `answer` = "No pudimos procesar tu consulta automáticamente. Un agente de soporte la va a revisar.", `confidence` = 0, `category` = `other`, `actions` = `["derivar_a_agente_humano"]`. Salida real de la CLI con un proveedor falso que siempre responde 429 (sin llamar a la API):

```json
{
  "answer": "No pudimos procesar tu consulta automáticamente. Un agente de soporte la va a revisar.",
  "confidence": 0.0,
  "category": "other",
  "actions": [
    "derivar_a_agente_humano"
  ]
}
```

Qué se reintenta y qué no:

| Error | ¿Se reintenta? | Qué pasa al agotarse |
|---|---|---|
| 429 (cuota o rate limit) | Sí, con backoff y `Retry-After` acotado | Respaldo, exit 0 |
| 5xx | Sí | Respaldo, exit 0 |
| Timeout o error de conexión | Sí | Respaldo, exit 0 |
| Respuesta sin JSON, JSON mal formado o fuera del contrato | Sí, hasta `max_parse_retries`, devolviendo el error al modelo | Respaldo, exit 0 |
| 400, 401, 403, 404 (clave inválida, pedido mal formado) | No | `Error: ...`, exit 1 |
| Falta la variable de la clave en `.env` | No | `Error: ...`, exit 1 |
| Consulta vacía | No | `Error: la consulta está vacía`, exit 1 |
| Escritura de métricas falla | No | `Aviso` en stderr; el JSON sale igual |

El SDK de Gemini no reintenta por su cuenta (`HttpRetryOptions(attempts=1)`), y el de OpenRouter tiene `max_retries=0`. Así el reintento lo controla el proyecto y se ve en `config/models.yaml`.

## Métricas y costo

Cada request de triage agrega una línea a `data/metrics.jsonl`, también cuando termina en respaldo (`fallback: true`). Es un archivo append-only, en UTF-8, que se versiona. La escribe la CLI después de `triage()`, así `triage()` no depende del disco. Si la escritura falla, la CLI avisa por stderr y el JSON sale igual.

No genera línea un error que no es transitorio (`ProviderError`, por ejemplo una clave inválida): no hay respuesta con tokens que contar. Un límite conocido: si un intento de validación consumió tokens y un intento posterior falla con ese tipo de error, esos tokens no se registran, porque la CLI sale con código 1.

| Campo | Pregunta que responde |
|---|---|
| `timestamp` | ¿Cuándo se hizo el request? ISO 8601 en UTC. |
| `source` | ¿Qué lo disparó? `cli` hoy; `eval` y `adversarial` cuando existan sus runners. |
| `provider`, `model` | ¿Qué proveedor y qué modelo respondieron? |
| `prompt_version` | ¿Con qué versión del prompt se generó la respuesta? |
| `prompt_tokens`, `completion_tokens`, `total_tokens` | ¿Cuántos tokens de entrada, de salida y en total consumió el request? Suma los de todos los intentos. En Gemini, `completion_tokens` incluye el razonamiento. |
| `latency_s` | ¿Cuánto esperó la persona? Tiempo de reloj desde que entra a `triage()` hasta la respuesta, incluidas las esperas de los reintentos. |
| `cost_usd` | ¿Cuánto se pagó? Tokens × precio real del modelo. Es 0 en los modelos gratuitos. |
| `cost_usd_list_price` | ¿Cuánto costaría lo mismo en un modelo pago de referencia? Mide el costo aunque hoy no se pague. |
| `reported_cost_usd` | ¿Qué costo informa el proveedor? Sirve para contrastar con `cost_usd`; `null` si no lo informa (Gemini no lo informa). |
| `attempts` | ¿Cuántas llamadas HTTP hizo el triage? Suma los reintentos de transporte y los de validación. |
| `fallback` | ¿Se devolvió la respuesta de respaldo? `true` si se agotaron los reintentos de validación o de transporte. |
| `category` | ¿Qué categoría asignó el modelo? En respaldo, `other`. Permite ver costo y latencia por categoría. |
| `guardrail` | ¿Qué guardrail bloqueó el request? `null` hasta que existan los guardrails. |

### Fórmula y precios

```text
cost_usd            = prompt_tokens × price_in_per_mtok / 1.000.000
                    + completion_tokens × price_out_per_mtok / 1.000.000

cost_usd_list_price = prompt_tokens × list_price.in_per_mtok / 1.000.000
                    + completion_tokens × list_price.out_per_mtok / 1.000.000
```

Se redondea a 8 decimales. Los precios están en `config/models.yaml`, en USD por millón de tokens:

| Precio | Modelo | Entrada | Salida | Fuente | Fecha |
|---|---|---|---|---|---|
| Real (`cost_usd`) | `nvidia/nemotron-3.5-super-vl:free` | 0 | 0 | https://openrouter.ai/api/v1/models | 2026-11-08 |
| Lista (`cost_usd_list_price`) | `nvidia/nemotron-3.5-super-vl` (pago) | 0,15 | 0,50 | https://openrouter.ai/api/v1/models | 2026-11-08 |
| Real (`cost_usd`) | `gemini-3.5-flash-lite` (nivel gratuito) | 0 | 0 | https://aistudio.google.com/docs/pricing | 2026-11-08 |
| Lista (`cost_usd_list_price`) | `gemini-3.5-flash-lite` (pago estándar, texto) | 0,30 | 2,50 | https://aistudio.google.com/docs/pricing | 2026-11-08 |

La referencia de lista de OpenRouter es la variante paga del mismo modelo, sin `:free`. El endpoint publica los precios en USD por token (`0.00000015` y `0.0000005`); se multiplican por 1.000.000. Para Gemini, la página de precios indica que el precio de salida incluye los tokens de razonamiento ("Output price (including thinking tokens)"). La página no muestra fecha de actualización: la fecha de la tabla es la de la consulta.

### Auditoría de una línea

Línea real de `data/metrics.jsonl` (primer ticket de la prueba de la Parte 3, facturación):

```json
{"timestamp": "2026-11-08T16:58:20+00:00", "source": "cli", "provider": "openrouter", "model": "nvidia/nemotron-3.5-super-vl:free", "prompt_version": "v1", "prompt_tokens": 647, "completion_tokens": 1426, "total_tokens": 2073, "latency_s": 39.192, "cost_usd": 0.0, "cost_usd_list_price": 0.00081005, "reported_cost_usd": 0.0, "attempts": 1, "fallback": false, "category": "billing", "guardrail": null}
```

Cuenta a mano:

```text
total_tokens        = 647 + 1.426                                   = 2.073        (registrado: 2073)

cost_usd            = 647 × 0 / 1.000.000 + 1.426 × 0 / 1.000.000   = 0            (registrado: 0.0)

cost_usd_list_price = 647 × 0,15 / 1.000.000 + 1.426 × 0,50 / 1.000.000
                    = 97,05 / 1.000.000 + 713 / 1.000.000
                    = 810,05 / 1.000.000                            = 0,00081005   (registrado: 0.00081005)
```

Línea real de Gemini (ticket de facturación del ejemplo de arriba), para la misma cuenta con el precio de lista de Gemini:

```text
cost_usd_list_price = 618 × 0,30 / 1.000.000 + 97 × 2,50 / 1.000.000
                    = 185,4 / 1.000.000 + 242,5 / 1.000.000
                    = 427,9 / 1.000.000                             = 0,0004279    (registrado: 0.0004279)
```

### Proyección a 400 tickets por día

Promedio de las dos ejecuciones con OpenRouter medidas en la Parte 3: 645,5 tokens de entrada y 1.085,5 de salida por ticket.

```text
por ticket (lista)  = 645,5 × 0,15 / 1.000.000 + 1.085,5 × 0,50 / 1.000.000 = 0,000639575 USD
400 tickets por día = 400 × 0,000639575                                    = 0,25583 USD/día
                    (≈ 7,67 USD por mes con 30 días)
costo real          = 0 USD/día (modelos gratuitos)
```

### Límites de esta medición

- Son pocas muestras. Los promedios y la proyección son orientativos hasta correr el dataset completo.
- La latencia fue de 39,2 s en el primer ticket de OpenRouter y de 9,3 s en el segundo. Las dos llamadas a Gemini de la Parte 4 tardaron 2,1 s y 2,0 s. Con pocas muestras no hay percentiles; p50 y p95 llegan con el runner de evals.
- Los intentos fallidos (429, 5xx, timeout) no aportan tokens porque no devuelven uso. Sus tokens no se cuentan.
- Si el modelo no tiene precio en `config/models.yaml`, `cost_usd` y `cost_usd_list_price` quedan en `null` y la CLI avisa por stderr.
- El cupo diario de OpenRouter depende de la compra de la cuenta: con 400 tickets por día, 1.000 requests alcanzan solo si la cuenta compró USD 10 o más; con menos, el cupo es 50 y los tickets excedentes devuelven 429 y terminan en respaldo.

## Arquitectura

```text
python -m src.main "<consulta>" [--provider] [--model] [--prompt]
        |
        v
src/main.py          parsea argumentos, carga .env y arma proveedor y prompt
        |
        v
src/triage.py        triage(query, provider, prompt, max_parse_retries) -> TriageResult
        |-- valida que la consulta no esté vacía
        |-- src/prompts.py        arma system + mensajes (ticket entre <ticket>)
        |-- provider.complete()   llama al LLM con el JSON Schema del contrato
        |     src/providers/      reintenta el transporte con backoff (429, 5xx, timeout)
        |-- src/parsing.py        extrae el primer objeto JSON y valida con SupportResponse
        |-- reintenta la validación o devuelve el respaldo
        |
        v
src/main.py          registra la línea en data/metrics.jsonl (src/metrics.py)
        |
        v
stdout: JSON {answer, confidence, category, actions}
stderr: avisos; "Error: ..." y código de salida 1 si algo impide responder
```

| Módulo | Responsabilidad |
|---|---|
| `src/main.py` | CLI: parsea argumentos, arma las dependencias, imprime el JSON o el error y registra la métrica. |
| `src/config.py` | Carga `.env` y `config/models.yaml`. |
| `src/schema.py` | Contrato `SupportResponse` (Pydantic). Su JSON Schema es el que se envía al modelo. |
| `src/parsing.py` | Extrae el primer objeto JSON de la respuesta (sin cercos de código ni texto alrededor) y lo valida. |
| `src/prompts.py` | Carga `prompts/*.yaml` y arma el `system` y los mensajes. |
| `src/triage.py` | Orquesta el flujo: reintento de validación, contrato de respaldo, tokens y latencia sumados de todos los intentos. |
| `src/metrics.py` | Costo (`estimate_cost`, precios de `config/models.yaml`) y registro append-only en `data/metrics.jsonl`. |
| `src/providers/base.py` | `LLMResponse`, `LLMProvider`, excepciones (`ProviderError`, `TransientProviderError`), backoff y tope de `Retry-After`. |
| `src/providers/openrouter.py` | Cliente de OpenRouter (SDK `openai` con la `base_url` de OpenRouter). |
| `src/providers/gemini.py` | Cliente de Gemini (SDK `google-genai`). Convierte sus errores en las excepciones del proyecto. |
| `src/providers/__init__.py` | Registro de proveedores (`PROVIDERS`) y `get_provider`. |
| `prompts/v1_zero_shot.yaml` | Prompt v1, zero-shot. |
| `config/models.yaml` | Valores por defecto, proveedores, modelos y precios (con fuente y fecha). |

## Pendiente

- Guardrails de entrada y de salida (Parte 8). Hoy un ticket puede contener `</ticket>` y cerrar el delimitador antes de tiempo.
- Dataset de evaluación y runner de evals (Partes 5 y 6).
- Confirmar los límites por minuto y por día de `gemini-3.5-flash-lite` en AI Studio.
- Registrar los tokens de intentos previos cuando un intento posterior falla con un error que no es transitorio.
