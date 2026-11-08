# Evals: openrouter / dots-studio/dots-3-note-preview:free / prompt v3

- Fecha: 2026-11-08T16:05:21
- Dataset: `evals/dataset.jsonl` (44 casos)
- Pausa entre requests: 3.2 s
- Guardrails: activados
- Caché: desactivada

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
| Válido al primer intento | 43 | 97.7 % |
| Válido tras reintento de validación | 1 | 2.3 % |
| Respaldo (contrato de fallback) | 0 | 0.0 % |

Un reintento de validación ocurre cuando la respuesta no cumple el contrato y se pide corregirla.
Un respaldo cuenta como `other`: si la esperada era `other`, suma como acierto. Por eso se informa aparte.

## Acciones

- Respuestas del modelo (sin respaldos): 44 casos, 66 acciones.
- Dentro del catálogo: 60 de 66 (90.9 %).
- Fuera del catálogo: `gestionar_usuos_y_permisos` (4), `actualizar_medio_de_pag` (1), `actualizar_medio_de pago` (1).
- Casos con acciones fuera del catálogo: t015, t019, t021, t025, t031, t039.

## Confianza

| Confianza del modelo | Casos | Accuracy |
|---|---|---|
| >= 0.8 | 44 | 100.0 % |
| < 0.8 | 0 | n/d |

Calibración: con confianza alta, la accuracy tiene que ser mayor. Los respaldos no entran.

## Operativas

| Métrica | Valor |
|---|---|
| Latencia media / p50 / p95 | 11.83 s / 11.03 s / 20.72 s |
| Tokens prompt / completion / total | 99902 / 39383 / 139285 |
| Casos servidos desde caché | 0 de 44 |
| Costo real total (USD) | 0.000000 |
| Costo a precio de lista total (USD) | 0.034677 |
| Costo por ticket, real / lista (USD) | 0.000000 / 0.000788 |
| Proyección a 400 tickets por día, real / lista (USD) | 0.000000 / 0.315244 |

La latencia de cada caso incluye los reintentos de transporte y sus esperas, como en `triage()`.

## Guardrails

Ninguna regla se activó.

Las métricas de promesas miden la respuesta final: con guardrails, después del reemplazo; con `--no-guardrails`, la del modelo.

## Casos fallados (0)

Ninguno.

## Promesas indebidas (0)

Ninguna.
