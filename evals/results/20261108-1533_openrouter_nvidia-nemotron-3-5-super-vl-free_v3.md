# Evals: openrouter / nvidia/nemotron-3.5-super-vl:free / prompt v3

- Fecha: 2026-11-08T15:33:01
- Dataset: `evals/dataset.jsonl` (44 casos)
- Pausa entre requests: 3.2 s
- Guardrails: activados

## Resultado global

| Métrica | Valor |
|---|---|
| Accuracy | 100.0 % (44 de 44) |
| Macro-F1 | 1.000 |
| Respaldos | 0 |
| Respuestas con promesas indebidas | 0.0 % (0 de 44) |

## Por categoría

| Categoría | Precision | Recall | F1 | Support | Predichos | Aciertos |
|---|---|---|---|---|---|---|
| billing | 100.0 % | 100.0 % | 1.000 | 11 | 11 | 11 |
| technical | 100.0 % | 100.0 % | 1.000 | 11 | 11 | 11 |
| account | 100.0 % | 100.0 % | 1.000 | 11 | 11 | 11 |
| other | 100.0 % | 100.0 % | 1.000 | 11 | 11 | 11 |

Precision = aciertos / predichos. Recall = aciertos / support.
F1 = 2 x precision x recall / (precision + recall). Sin predicciones o sin casos, la métrica queda en 0.

## Matriz de confusión

Filas: categoría esperada. Columnas: categoría predicha. Un respaldo cuenta como `other`.

| esperada \ predicha | billing | technical | account | other | Total |
|---|---|---|---|---|---|
| billing | 11 | 0 | 0 | 0 | 11 |
| technical | 0 | 11 | 0 | 0 | 11 |
| account | 0 | 0 | 11 | 0 | 11 |
| other | 0 | 0 | 0 | 11 | 11 |
| **Total** | 11 | 11 | 11 | 11 | 44 |

## Contrato

| Resultado | Casos | % |
|---|---|---|
| Válido al primer intento | 44 | 100.0 % |
| Válido tras reintento de validación | 0 | 0.0 % |
| Respaldo (contrato de fallback) | 0 | 0.0 % |

Un reintento de validación ocurre cuando la respuesta no cumple el contrato y se pide corregirla.
Un respaldo cuenta como `other`: si la esperada era `other`, suma como acierto. Por eso se informa aparte.

## Acciones

- Respuestas del modelo (sin respaldos): 44 casos, 64 acciones.
- Dentro del catálogo: 64 de 64 (100.0 %).
- Fuera del catálogo: ninguna.

## Confianza

| Confianza del modelo | Casos | Accuracy |
|---|---|---|
| >= 0.8 | 41 | 100.0 % |
| < 0.8 | 3 | 100.0 % |

Calibración: con confianza alta, la accuracy tiene que ser mayor. Los respaldos no entran.

## Operativas

| Métrica | Valor |
|---|---|
| Latencia media / p50 / p95 | 5.51 s / 3.82 s / 18.65 s |
| Tokens prompt / completion / total | 99954 / 18477 / 118431 |
| Costo real total (USD) | 0.000000 |
| Costo a precio de lista total (USD) | 0.024232 |
| Costo por ticket, real / lista (USD) | 0.000000 / 0.000551 |
| Proyección a 400 tickets por día, real / lista (USD) | 0.000000 / 0.220287 |

La latencia de cada caso incluye los reintentos de transporte y sus esperas, como en `triage()`.

## Guardrails

Ninguna regla se activó.

Las métricas de promesas miden la respuesta final: con guardrails, después del reemplazo; con `--no-guardrails`, la del modelo.

## Casos fallados (0)

Ninguno.

## Promesas indebidas (0)

Ninguna.
