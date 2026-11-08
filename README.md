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

## Arquitectura

```text
python -m src.main "<consulta>"
        |
        v
src/main.py          parsea argumentos, carga .env y arma proveedor y prompt
        |
        v
src/triage.py        triage(query, provider, prompt)
        |-- valida que la consulta no esté vacía
        |-- src/prompts.py        arma system + mensajes (ticket entre <ticket>)
        |-- provider.complete()   llama al LLM con el JSON Schema del contrato
        |     src/providers/openrouter.py   reintenta con backoff ante 429, 5xx y timeout
        |-- src/schema.py         SupportResponse.model_validate_json()
        |
        v
stdout: JSON {answer, confidence, category, actions}
stderr: "Error: ..." y código de salida 1 si algo falla
```

| Módulo | Responsabilidad |
|---|---|
| `src/main.py` | CLI: parsea argumentos, arma las dependencias e imprime el JSON o el error. |
| `src/config.py` | Carga `.env` y `config/models.yaml`. |
| `src/schema.py` | Contrato `SupportResponse` (Pydantic). Su JSON Schema es el que se envía al modelo. |
| `src/prompts.py` | Carga `prompts/*.yaml` y arma el `system` y los mensajes. |
| `src/triage.py` | Orquesta el flujo con el proveedor y el prompt ya construidos. |
| `src/providers/base.py` | `LLMResponse`, `LLMProvider`, excepciones y backoff. |
| `src/providers/openrouter.py` | Cliente de OpenRouter (SDK `openai` con la `base_url` de OpenRouter). |
| `src/providers/__init__.py` | Registro de proveedores y `get_provider`. |
| `prompts/v1_zero_shot.yaml` | Prompt v1, zero-shot. |
| `config/models.yaml` | Valores por defecto, proveedores y modelos. |

Pendiente: todavía no hay reintento ante JSON inválido, métricas en `data/metrics.jsonl` ni guardrails.
