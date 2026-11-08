# Evals: openrouter / nvidia/nemotron-3.5-super-vl:free / prompt v3

- Fecha: 2026-11-08T15:52:41
- Dataset: `evals/holdout.jsonl` (16 casos)
- Pausa entre requests: 3.2 s
- Guardrails: activados

## Resultado global

| Métrica | Valor |
|---|---|
| Accuracy | 100.0 % (16 de 16) |
| Macro-F1 | 1.000 |
| Respaldos | 0 |
| Respuestas con promesas indebidas | 0.0 % (0 de 16) |

## Por categoría

| Categoría | Precision | Recall | F1 | Support | Predichos | Aciertos |
|---|---|---|---|---|---|---|
| billing | 100.0 % | 100.0 % | 1.000 | 4 | 4 | 4 |
| technical | 100.0 % | 100.0 % | 1.000 | 4 | 4 | 4 |
| account | 100.0 % | 100.0 % | 1.000 | 4 | 4 | 4 |
| other | 100.0 % | 100.0 % | 1.000 | 4 | 4 | 4 |

Precision = aciertos / predichos. Recall = aciertos / support.
F1 = 2 x precision x recall / (precision + recall). Sin predicciones o sin casos, la métrica queda en 0.

## Matriz de confusión

Filas: categoría esperada. Columnas: categoría predicha. Un respaldo cuenta como `other`.

| esperada \ predicha | billing | technical | account | other | Total |
|---|---|---|---|---|---|
| billing | 4 | 0 | 0 | 0 | 4 |
| technical | 0 | 4 | 0 | 0 | 4 |
| account | 0 | 0 | 4 | 0 | 4 |
| other | 0 | 0 | 0 | 4 | 4 |
| **Total** | 4 | 4 | 4 | 4 | 16 |

## Contrato

| Resultado | Casos | % |
|---|---|---|
| Válido al primer intento | 16 | 100.0 % |
| Válido tras reintento de validación | 0 | 0.0 % |
| Respaldo (contrato de fallback) | 0 | 0.0 % |

Un reintento de validación ocurre cuando la respuesta no cumple el contrato y se pide corregirla.
Un respaldo cuenta como `other`: si la esperada era `other`, suma como acierto. Por eso se informa aparte.

## Acciones

- Respuestas del modelo (sin respaldos): 16 casos, 23 acciones.
- Dentro del catálogo: 23 de 23 (100.0 %).
- Fuera del catálogo: ninguna.

## Confianza

| Confianza del modelo | Casos | Accuracy |
|---|---|---|
| >= 0.8 | 15 | 100.0 % |
| < 0.8 | 1 | 100.0 % |

Calibración: con confianza alta, la accuracy tiene que ser mayor. Los respaldos no entran.

## Operativas

| Métrica | Valor |
|---|---|
| Latencia media / p50 / p95 | 5.23 s / 4.82 s / 9.59 s |
| Tokens prompt / completion / total | 36389 / 7412 / 43801 |
| Costo real total (USD) | 0.000000 |
| Costo a precio de lista total (USD) | 0.009164 |
| Costo por ticket, real / lista (USD) | 0.000000 / 0.000573 |
| Proyección a 400 tickets por día, real / lista (USD) | 0.000000 / 0.229109 |

La latencia de cada caso incluye los reintentos de transporte y sus esperas, como en `triage()`.

## Guardrails

Ninguna regla se activó.

Las métricas de promesas miden la respuesta final: con guardrails, después del reemplazo; con `--no-guardrails`, la del modelo.

## Casos fallados (0)

Ninguno.

## Promesas indebidas (0)

Ninguna.
