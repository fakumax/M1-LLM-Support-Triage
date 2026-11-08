# Métricas y costos

Cada request de triage agrega una línea a `data/metrics.jsonl`. El archivo es append-only, UTF-8 y está versionado. Lo escribe `src/pipeline.py` después de `triage()`, así que `triage()` no depende del disco. Si la escritura falla, se avisa por stderr y el JSON sale igual.

No genera línea un error que no es transitorio (`ProviderError`, por ejemplo una clave inválida), porque no hubo respuesta con tokens que contar. Límite conocido: si un intento de validación consumió tokens y después un intento falla con ese tipo de error, esos tokens no se registran, porque la CLI sale con código 1.

Las 315 primeras líneas del archivo no tienen el campo `cached`, que se agregó con la caché. Quien lea el archivo tiene que tratar la ausencia como `false`.

## Campos

| Campo | Pregunta que responde |
|---|---|
| `timestamp` | ¿Cuándo terminó el request? Es la hora UTC en que se arma el registro, justo después de `triage()`, así que incluye los reintentos. ISO 8601. |
| `source` | ¿Qué lo disparó? `cli` para la CLI, `eval` para el runner de evals y `adversarial` para la suite de ataques. |
| `provider`, `model` | ¿Qué proveedor y qué modelo respondieron? |
| `prompt_version` | ¿Con qué versión del prompt se generó la respuesta? |
| `prompt_tokens`, `completion_tokens`, `total_tokens` | ¿Cuántos tokens de entrada, de salida y en total consumió el request? Suma los de todos los intentos. En Gemini, `completion_tokens` incluye el razonamiento. |
| `latency_s` | ¿Cuánto esperó la persona? Tiempo de reloj desde que entra a `triage()` hasta la respuesta, con las esperas de los reintentos. |
| `cost_usd` | ¿Cuánto se pagó? Tokens × precio real del modelo. Es 0 en los modelos gratuitos y en los aciertos de caché. |
| `cost_usd_list_price` | ¿Cuánto costaría lo mismo en un modelo pago de referencia? Mide el costo aunque hoy no se pague. |
| `reported_cost_usd` | ¿Qué costo informa el proveedor? Sirve para contrastar con `cost_usd`. Es `null` si no lo informa (Gemini no lo informa). |
| `attempts` | ¿Cuántas llamadas HTTP hizo el triage? Suma los reintentos de transporte y los de validación. |
| `cached` | ¿La respuesta salió de `data/cache/`? Es `true` si ninguna llamada del triage llegó a la API. Su costo es 0 y `attempts` es 0, con los tokens originales. |
| `fallback` | ¿Se devolvió la respuesta de respaldo? Es `true` si se agotaron los reintentos de validación o de transporte, o si un guardrail bloqueó la consulta. |
| `category` | ¿Qué categoría quedó en la respuesta final? En respaldo, `other`. Permite ver costo y latencia por categoría. |
| `guardrail` | Lista de los códigos de guardrail que se activaron, o `null` si ninguno. Ver [seguridad.md](seguridad.md). |

## Fórmula

```text
cost_usd            = prompt_tokens × price_in_per_mtok / 1.000.000
                    + completion_tokens × price_out_per_mtok / 1.000.000

cost_usd_list_price = prompt_tokens × list_price.in_per_mtok / 1.000.000
                    + completion_tokens × list_price.out_per_mtok / 1.000.000
```

Se redondea a 8 decimales. Los precios están en `config/models.yaml`, en USD por millón de tokens, con la URL de origen y la fecha de cada precio.

## Precios

| Precio | Modelo | Entrada | Salida | Fuente | Fecha |
|---|---|---|---|---|---|
| Real (`cost_usd`) | `nvidia/nemotron-3.5-super-vl:free` | 0 | 0 | https://openrouter.ai/api/v1/models | 2026-11-08 |
| Lista (`cost_usd_list_price`) | `nvidia/nemotron-3.5-super-vl` (pago) | 0,15 | 0,50 | https://openrouter.ai/api/v1/models | 2026-11-08 |
| Real (`cost_usd`) | `gemini-3.5-flash-lite` (nivel gratuito) | 0 | 0 | https://aistudio.google.com/docs/pricing | 2026-11-08 |
| Lista (`cost_usd_list_price`) | `gemini-3.5-flash-lite` (pago estándar, texto) | 0,30 | 2,50 | https://aistudio.google.com/docs/pricing | 2026-11-08 |
| Real (`cost_usd`) | `dots-studio/dots-3-note-preview:free` | 0 | 0 | https://openrouter.ai/api/v1/models | 2026-11-08 |
| Lista (`cost_usd_list_price`) | `nvidia/nemotron-3.5-super-vl` como referencia para dots (no tiene variante paga) | 0,15 | 0,50 | https://openrouter.ai/api/v1/models | 2026-11-08 |

- La referencia de lista de OpenRouter es la variante paga del mismo modelo, sin `:free`. El endpoint publica los precios en USD por token (`0.00000015` y `0.0000005`); se multiplican por 1.000.000.
- Dots no tiene variante paga. Se usa Nemotron como aproximación de tamaño (12.000 millones de parámetros activos frente a 16.000 de dots). Es una referencia, no el precio real de dots.
- Para Gemini, la página de precios indica que el precio de salida incluye los tokens de razonamiento. La página no muestra fecha de actualización: la fecha de la tabla es la de la consulta.

## Auditoría de una línea

Línea real de `data/metrics.jsonl`: primer ticket de la CLI (facturación, prompt v1, OpenRouter).

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

Misma cuenta con Gemini, para el ticket de facturación del ejemplo de la CLI con `--provider gemini`, con el precio de lista de Gemini (línea real: 618 tokens de entrada y 97 de salida):

```text
cost_usd_list_price = 618 × 0,30 / 1.000.000 + 97 × 2,50 / 1.000.000
                    = 185,4 / 1.000.000 + 242,5 / 1.000.000
                    = 427,9 / 1.000.000                             = 0,0004279    (registrado: 0.0004279)
```

## Proyección a 400 tickets por día

Costo a precio de lista. El costo real es 0 en todos los casos, porque los modelos son gratuitos.

| Base de cálculo | Costo por ticket (USD) | 400 tickets por día (USD) | Mensual con 30 días (USD) |
|---|---|---|---|
| Dos tickets de la CLI con OpenRouter (promedio de 645,5 tokens de entrada y 1.085,5 de salida) | 0,000639575 | 0,25583 | 7,67 |
| Nemotron, v3, 44 casos con guardrails | 0,000551 | 0,220287 | 6,61 |
| Gemini `gemini-3.5-flash-lite`, v3, 44 casos con guardrails | 0,000843 | 0,337125 | 10,11 |
| Dots, v3, 44 casos con guardrails | 0,000788 | 0,315244 | 9,46 |

La fila de dos tickets es una estimación con muestra chica. Las demás salen de corridas completas de `evals/results/` (`total de costo de lista / 44 tickets`).

## Límites de la medición

- Son pocas muestras. La proyección de dos tickets es orientativa; las corridas completas de 44 casos dan una base más firme.
- La latencia del primer ticket de OpenRouter fue de 39,2 s y la del segundo de 9,3 s. Las dos llamadas a Gemini de la prueba tardaron 2,1 s y 2,0 s. Los percentiles se calculan sobre el dataset completo (ver [evals.md](evals.md)).
- Los intentos fallidos (429, 5xx, timeout) no aportan tokens porque no devuelven uso. Sus tokens no se cuentan.
- Si el modelo no tiene precio en `config/models.yaml`, `cost_usd` y `cost_usd_list_price` quedan en `null` y la CLI avisa por stderr.
- El cupo diario de OpenRouter depende de la compra de la cuenta: 50 requests por día si se compraron menos de USD 10 en créditos, y 1.000 si se compraron USD 10 o más. Con 400 tickets por día, el cupo de 50 no alcanza.
- Con la caché activada, un acierto tiene costo 0 en ambas columnas y conserva los tokens originales para auditar lo que costó la respuesta guardada.
