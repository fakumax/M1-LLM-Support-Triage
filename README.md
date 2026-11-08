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

Salida de una ejecución real (prompt `v1`, modelo por defecto):

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

El JSON sale solo por stdout. Los errores van a stderr con código de salida 1:

```
Error: la consulta está vacía
```

Opciones:

| Opción | Descripción | Por defecto |
|---|---|---|
| `--provider` | Proveedor LLM registrado en `src/providers/__init__.py` | `openrouter` |
| `--model` | ID del modelo del proveedor | `nvidia/nemotron-3.5-super-vl:free` |
| `--prompt` | Versión del prompt en `prompts/` | `v1` |

Solo se usan modelos `:free` de OpenRouter. Los valores por defecto están en `config/models.yaml`:

| Parámetro | Valor | Por qué |
|---|---|---|
| `temperature` | 0 | Reduce la variación de la clasificación entre corridas del mismo ticket. |
| `max_tokens` | 2000 | Los modelos gratuitos razonan antes de responder (400 a 1.500 tokens); con menos, el JSON llega cortado. |
| `timeout_s` | 60 | Margen para la latencia de los modelos gratuitos (en dos pruebas de esta etapa tardaron 4,6 y 5,0 s). |
| `max_api_retries` | 3 | Reintentos ante 429, 5xx y timeouts, con esperas de 1, 2 y 4 s, o el `Retry-After` del servidor. |

## Métricas y costo

Cada request de triage que termina con una respuesta agrega una línea a `data/metrics.jsonl`. Es un archivo append-only, en UTF-8, que se versiona. La escribe la CLI después de `triage()`, así `triage()` no depende del disco. Si la escritura falla, la CLI avisa por stderr y el JSON sale igual.

No generan línea los requests que fallan con `ProviderError` (clave inválida, error 400, o 429, 5xx y timeouts agotados los reintentos), porque no hay respuesta con tokens que contar. Tampoco la genera una respuesta que no cumple el contrato (`TriageError`): el modelo consumió tokens y ese costo queda sin contar hasta que exista el respaldo.

| Campo | Pregunta que responde |
|---|---|
| `timestamp` | ¿Cuándo se hizo el request? ISO 8601 en UTC. |
| `source` | ¿Qué lo disparó? `cli` hoy; `eval` y `adversarial` cuando existan sus runners. |
| `provider`, `model` | ¿Qué proveedor y qué modelo respondieron? |
| `prompt_version` | ¿Con qué versión del prompt se generó la respuesta? |
| `prompt_tokens`, `completion_tokens`, `total_tokens` | ¿Cuántos tokens de entrada, de salida y en total consumió el request? |
| `latency_s` | ¿Cuánto esperó la persona? Tiempo de reloj desde que entra a `triage()` hasta la respuesta, incluidas las esperas de los reintentos. |
| `cost_usd` | ¿Cuánto se pagó? Tokens × precio real del modelo. Es 0 en los modelos `:free`. |
| `cost_usd_list_price` | ¿Cuánto costaría lo mismo en un modelo pago de referencia? Mide el costo aunque hoy no se pague. |
| `reported_cost_usd` | ¿Qué costo informa el proveedor? Sirve para contrastar con `cost_usd`; `null` si no lo informa. |
| `attempts` | ¿Cuántas llamadas HTTP hizo el triage? Hoy cuenta los reintentos de transporte. |
| `fallback` | ¿Se devolvió la respuesta de respaldo? Siempre `false` hasta que exista el respaldo. |
| `category` | ¿Qué categoría asignó el modelo? Permite ver costo y latencia por categoría. |
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

La referencia de lista es la variante paga del mismo modelo, sin `:free`. El endpoint publica los precios en USD por token (`0.00000015` y `0.0000005`); se multiplican por 1.000.000.

### Auditoría de una línea

Línea real de `data/metrics.jsonl` (primer ticket de la prueba de esta etapa, facturación):

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

### Proyección a 400 tickets por día

Promedio de las dos ejecuciones medidas: 645,5 tokens de entrada y 1.085,5 de salida por ticket.

```text
por ticket (lista)  = 645,5 × 0,15 / 1.000.000 + 1.085,5 × 0,50 / 1.000.000 = 0,000639575 USD
400 tickets por día = 400 × 0,000639575                                    = 0,25583 USD/día
                    (≈ 7,67 USD por mes con 30 días)
costo real          = 0 USD/día (modelos :free)
```

### Límites de esta medición

- Son dos requests. Los promedios y la proyección son orientativos hasta correr el dataset completo.
- La latencia fue de 39,2 s en el primer ticket y de 9,3 s en el segundo. Con dos muestras no hay percentiles; p50 y p95 llegan con el runner de evals.
- Los intentos fallidos (429, 5xx, timeout) no aportan tokens porque no devuelven uso. Sus tokens no se cuentan.
- Si el modelo no tiene precio en `config/models.yaml`, `cost_usd` y `cost_usd_list_price` quedan en `null` y la CLI avisa por stderr.
- El cupo diario de los modelos `:free` no lo controla el proyecto. Con 400 tickets por día hay que confirmarlo en la cuenta de OpenRouter.

## Arquitectura

```text
python -m src.main "<consulta>"
        |
        v
src/main.py          parsea argumentos, carga .env y arma proveedor y prompt
        |
        v
src/triage.py        triage(query, provider, prompt) -> TriageResult (latencia total e intentos)
        |-- valida que la consulta no esté vacía
        |-- src/prompts.py        arma system + mensajes (ticket entre <ticket>)
        |-- provider.complete()   llama al LLM con el JSON Schema del contrato
        |     src/providers/openrouter.py   reintenta con backoff ante 429, 5xx y timeout
        |-- src/schema.py         SupportResponse.model_validate_json()
        |
        v
src/main.py          registra la línea en data/metrics.jsonl (src/metrics.py)
        |
        v
stdout: JSON {answer, confidence, category, actions}
stderr: "Error: ..." y código de salida 1 si algo falla
```

| Módulo | Responsabilidad |
|---|---|
| `src/main.py` | CLI: parsea argumentos, arma las dependencias, imprime el JSON o el error y registra la métrica. |
| `src/config.py` | Carga `.env` y `config/models.yaml`. |
| `src/schema.py` | Contrato `SupportResponse` (Pydantic). Su JSON Schema es el que se envía al modelo. |
| `src/prompts.py` | Carga `prompts/*.yaml` y arma el `system` y los mensajes. |
| `src/triage.py` | Orquesta el flujo con el proveedor y el prompt ya construidos. Mide la latencia total y devuelve los intentos. |
| `src/metrics.py` | Costo (`estimate_cost`, precios de `config/models.yaml`) y registro append-only en `data/metrics.jsonl`. |
| `src/providers/base.py` | `LLMResponse` (con `attempts`), `LLMProvider`, excepciones y backoff. |
| `src/providers/openrouter.py` | Cliente de OpenRouter (SDK `openai` con la `base_url` de OpenRouter). |
| `src/providers/__init__.py` | Registro de proveedores y `get_provider`. |
| `prompts/v1_zero_shot.yaml` | Prompt v1, zero-shot. |
| `config/models.yaml` | Valores por defecto, proveedores, modelos y precios (con fuente y fecha). |

Pendiente: todavía no hay reintento ante JSON inválido ni guardrails.
