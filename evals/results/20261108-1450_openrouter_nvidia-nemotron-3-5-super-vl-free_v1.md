# Evals: openrouter / nvidia/nemotron-3.5-super-vl:free / prompt v1

- Fecha: 2026-11-08T14:50:25
- Dataset: `evals/dataset.jsonl` (44 casos)
- Pausa entre requests: 3.2 s

## Resultado global

| Métrica | Valor |
|---|---|
| Accuracy | 97.7 % (43 de 44) |
| Macro-F1 | 0.977 |
| Respaldos | 0 |
| Respuestas con promesas indebidas | 0.0 % (0 de 44) |

## Por categoría

| Categoría | Precision | Recall | F1 | Support | Predichos | Aciertos |
|---|---|---|---|---|---|---|
| billing | 91.7 % | 100.0 % | 0.957 | 11 | 12 | 11 |
| technical | 100.0 % | 90.9 % | 0.952 | 11 | 10 | 10 |
| account | 100.0 % | 100.0 % | 1.000 | 11 | 11 | 11 |
| other | 100.0 % | 100.0 % | 1.000 | 11 | 11 | 11 |

Precision = aciertos / predichos. Recall = aciertos / support.
F1 = 2 x precision x recall / (precision + recall). Sin predicciones o sin casos, la métrica queda en 0.

## Matriz de confusión

Filas: categoría esperada. Columnas: categoría predicha. Un respaldo cuenta como `other`.

| esperada \ predicha | billing | technical | account | other | Total |
|---|---|---|---|---|---|
| billing | 11 | 0 | 0 | 0 | 11 |
| technical | 1 | 10 | 0 | 0 | 11 |
| account | 0 | 0 | 11 | 0 | 11 |
| other | 0 | 0 | 0 | 11 | 11 |
| **Total** | 12 | 10 | 11 | 11 | 44 |

## Contrato

| Resultado | Casos | % |
|---|---|---|
| Válido al primer intento | 44 | 100.0 % |
| Válido tras reintento de validación | 0 | 0.0 % |
| Respaldo (contrato de fallback) | 0 | 0.0 % |

Un reintento de validación ocurre cuando la respuesta no cumple el contrato y se pide corregirla.
Un respaldo cuenta como `other`: si la esperada era `other`, suma como acierto. Por eso se informa aparte.

## Acciones

- Respuestas del modelo (sin respaldos): 44 casos, 80 acciones.
- Dentro del catálogo: 80 de 80 (100.0 %).
- Fuera del catálogo: ninguna.

## Confianza

| Confianza del modelo | Casos | Accuracy |
|---|---|---|
| >= 0.8 | 42 | 97.6 % |
| < 0.8 | 2 | 100.0 % |

Calibración: con confianza alta, la accuracy tiene que ser mayor. Los respaldos no entran.

## Operativas

| Métrica | Valor |
|---|---|
| Latencia media / p50 / p95 | 6.57 s / 6.31 s / 10.80 s |
| Tokens prompt / completion / total | 28850 / 30886 / 59736 |
| Costo real total (USD) | 0.000000 |
| Costo a precio de lista total (USD) | 0.019770 |
| Costo por ticket, real / lista (USD) | 0.000000 / 0.000449 |
| Proyección a 400 tickets por día, real / lista (USD) | 0.000000 / 0.179732 |

La latencia de cada caso incluye los reintentos de transporte y sus esperas, como en `triage()`.

## Casos fallados (1)

| id | esperada | predicha | confianza | respaldo | query |
|---|---|---|---|---|---|
| t022 | technical | billing | 0.80 | no | ¡Hace tres días que no puedo facturar porque el punto de venta no abre! Y encima me cobra… |

## Promesas indebidas (0)

Ninguna.
