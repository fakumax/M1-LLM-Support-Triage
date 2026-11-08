# Evals

Cómo se corre la suite, qué mide cada métrica y el resultado de cada corrida. Todos los números salen de los reportes en `evals/results/` (un `.json` con el detalle y un `.md` con las tablas por corrida).

## Cómo correr

```powershell
python -m evals.runner
```

| Opción | Descripción | Por defecto |
|---|---|---|
| `--suite` | `dataset` clasifica los 44 casos. `adversarial` corre los 20 casos de `evals/adversarial.jsonl` con guardrails y sin guardrails, en una sola corrida. Con `adversarial` no se admiten `--no-guardrails` ni `--cache`. | `dataset` |
| `--provider` | `openrouter` o `gemini` | `openrouter` |
| `--model` | ID del modelo. Con OpenRouter tiene que terminar en `:free`; el runner lo verifica antes de llamar a la API. | `default_model` del proveedor |
| `--prompt` | Versión del prompt en `prompts/` | `v3` |
| `--dataset RUTA` | JSONL a evaluar. Si no es el default, el nombre del reporte agrega el nombre del archivo (por ejemplo `_holdout`). | `evals/dataset.jsonl`, o `evals/adversarial.jsonl` con `--suite adversarial` |
| `--limit N` | Evalúa solo los primeros N casos. No guarda reportes. Con pocos casos el macro-F1 no es comparable: las categorías sin casos suman 0. | todos |
| `--sleep S` | Segundos de pausa después de cada llamada a la API. No se espera después de un acierto de caché ni de un bloqueo de guardrail. | 3,2 s en OpenRouter y 4,5 s en Gemini (`eval_sleep_s` en `config/models.yaml`) |
| `--no-guardrails` | Desactiva los guardrails. El reporte lleva el sufijo `_sin-guardrails`. | Guardrails activados |
| `--cache` | Reutiliza respuestas de `data/cache/`. El reporte indica cuántos casos salieron de la caché. | Desactivado |

El progreso de cada caso va a stderr y el reporte en Markdown va a stdout. Una corrida completa del dataset tarda unos 8 minutos con OpenRouter (44 requests y las pausas). Cada corrida completa guarda `evals/results/<AAAAmmdd-HHMM>_<proveedor>_<modelo>_<prompt>[_<dataset>][_sin-guardrails].json` y `.md`.

Para reproducir cada corrida del repositorio, desde la raíz en PowerShell:

```powershell
python -m evals.runner --prompt v1
python -m evals.runner --prompt v2
python -m evals.runner --prompt v3
python -m evals.runner --prompt v1 --dataset evals/holdout.jsonl
python -m evals.runner --prompt v3 --dataset evals/holdout.jsonl
python -m evals.runner --provider gemini
python -m evals.runner --model dots-studio/dots-3-note-preview:free
python -m evals.runner --suite adversarial
```

## Corridas guardadas

| Fecha y hora (local) | Modelo | Prompt | Dataset | Guardrails | Archivo base en `evals/results/` |
|---|---|---|---|---|---|
| 08/11 14:28 | nemotron (OpenRouter) | v1 | 44 casos | no (anterior a los guardrails) | `20261108-1428_openrouter_nvidia-nemotron-3-5-super-vl-free_v1` |
| 08/11 14:50 | nemotron | v1 | 44 casos | no | `20261108-1450_..._v1` (segunda corrida, para medir el ruido) |
| 08/11 14:57 | nemotron | v2 | 44 casos | no | `20261108-1457_..._v2` |
| 08/11 15:03 | nemotron | v3 | 44 casos | no | `20261108-1503_..._v3` |
| 08/11 15:09 | nemotron | v3 | 44 casos | no | `20261108-1509_..._v3` (segunda corrida) |
| 08/11 15:33 | nemotron | v3 | 44 casos | sí | `20261108-1533_..._v3` |
| 08/11 15:50 | nemotron | v1 | holdout, 16 casos | sí | `20261108-1550_..._v1_holdout` |
| 08/11 15:52 | nemotron | v3 | holdout, 16 casos | sí | `20261108-1552_..._v3_holdout` |
| 08/11 16:00 | `gemini-3.5-flash-lite` | v3 | 44 casos | sí | `20261108-1600_gemini_gemini-3-5-flash-lite_v3` |
| 08/11 16:05 | `dots-3-note-preview` | v3 | 44 casos | sí | `20261108-1605_openrouter_dots-studio-dots-3-note-preview-free_v3` |
| 08/11 16:33 | nemotron | v3 | adversarial, 20 casos | con y sin | `20261108-1633_..._v3_adversarial` |

Todas las corridas usan `temperature` 0 y `max_tokens` 2000. Las de 14:28 a 15:09 se hicieron antes de los guardrails.

## Qué mide cada métrica

| Métrica | Qué responde | Por qué importa en este caso |
|---|---|---|
| Accuracy | ¿Qué fracción de los tickets cayó en la categoría correcta? | Es fácil de leer, pero puede engañar si las clases están desbalanceadas. El dataset tiene 11 casos por categoría. |
| Precision por categoría | De los tickets que el sistema marca como X, ¿cuántos son X? | Precision baja en `billing` significa que el agente recibe como cobros tickets de otra cola. |
| Recall por categoría | De los tickets que son X, ¿cuántos encuentra el sistema? | Recall bajo en `billing` significa cobros mal derivados: el error más caro para el cliente. |
| F1 | Media armónica de precision y recall | Resume una categoría en un número sin que una compense a la otra. |
| Macro-F1 | Promedio del F1 de las cuatro categorías | Cada categoría pesa lo mismo: una categoría floja no se tapa con las demás. |
| Matriz de confusión | Cuántas veces una categoría esperada salió como otra | Muestra qué pares se confunden. |
| Contrato | % válido al primer intento, válido tras reintento y respaldo | Un contrato roto obliga a reintentar o deja al agente con un respaldo en vez de una propuesta. |
| Acciones dentro del catálogo | % de acciones que están en `ACTION_CATALOG` | Una acción fuera del catálogo no se puede asociar a un procedimiento del agente. |
| Calibración | Accuracy con confianza mayor o igual a 0,8, y con confianza menor | Si la confianza no separa aciertos de errores, no sirve para decidir qué tickets pasan a revisión humana. |
| Latencia media, p50 y p95 | Cuánto espera la persona | El p95 es la espera de los peores casos. |
| Tokens, costo real y a precio de lista | Cuánto consume cada ticket y cuánto costaría | Base de la proyección a 400 tickets por día ([metricas-y-costos.md](metricas-y-costos.md)). |
| Respuestas con promesas indebidas | ¿La respuesta promete o afirma reintegros, descuentos, plazos o aprobaciones que el agente todavía no decidió? | El cliente toma ese texto como compromiso. `src/policy.py` la detecta con patrones en español, portugués e inglés. |

Un caso que termina en respaldo cuenta como predicción `other`, que es lo que devolvió el sistema, y se informa aparte. Si la categoría esperada era `other`, suma como acierto; por eso el reporte lo muestra por separado.

## Línea base: prompt v1 (primera corrida, 14:28)

Prompt v1 (zero-shot) con `nvidia/nemotron-3.5-super-vl:free`, 44 casos.

| Métrica global | Valor |
|---|---|
| Accuracy | 95,5 % (42 de 44) |
| Macro-F1 | 0,954 |
| Respaldos | 0 |
| Válido al primer intento | 44 de 44 |
| Acciones dentro del catálogo | 81 de 81 |
| Calibración: confianza ≥ 0,8 / < 0,8 | 97,7 % (43 casos) / 0 % (1 caso) |
| Latencia media / p50 / p95 | 7,36 s / 5,48 s / 16,60 s |
| Tokens (entrada / salida) | 28.850 / 29.094 |
| Costo real / a precio de lista | 0 USD / 0,018874 USD en total |
| Proyección a 400 tickets por día (precio de lista) | 0,171586 USD por día |

| Categoría | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| `billing` | 90,9 % | 90,9 % | 0,909 | 11 |
| `technical` | 100,0 % | 90,9 % | 0,952 | 11 |
| `account` | 100,0 % | 100,0 % | 1,000 | 11 |
| `other` | 91,7 % | 100,0 % | 0,957 | 11 |

Matriz de confusión (filas: esperada; columnas: predicha):

| esperada \ predicha | billing | technical | account | other | Total |
|---|---|---|---|---|---|
| billing | 10 | 0 | 0 | 1 | 11 |
| technical | 1 | 10 | 0 | 0 | 11 |
| account | 0 | 0 | 11 | 0 | 11 |
| other | 0 | 0 | 0 | 11 | 11 |
| **Total** | 11 | 10 | 11 | 12 | 44 |

Cómo leerla: la fila `billing` tiene 11 cobros esperados, 10 salen como billing y uno (t033) como other, así que el recall de billing es 10/11 = 90,9 %. La columna `billing` tiene 11 predicciones de billing, 10 aciertos y uno (t022, que era technical), así que la precision también es 90,9 %. La fila `technical`, columna `billing`, es el error de t022: por eso technical tiene recall 10/11 y precision 100 %.

Casos fallados:

| id | esperada | predicha | confianza | Query (recortada) |
|---|---|---|---|---|
| t022 | technical | billing | 0,75 | ¡Hace tres días que no puedo facturar porque el punto de venta no abre! Y encima me cobra… |
| t033 | billing | other | 0,85 | Hola, ¿cuánto me sale por mes el plan que tengo contratado? Lo necesito para cerrar el pr… |

Hipótesis que llevaron a v3:

- **t022** es multi-intención (regla 1 de los criterios): la caída del punto de venta es la causa y el reintegro es consecuencia. El v1 no tiene reglas de desempate y `reintegros` figura en la definición de `billing`, así que el modelo se quedó con el pedido de plata. Eligió `gestionar_reintegro` y no escaló a soporte técnico.
- **t033** pregunta cuánto cuesta el plan que el cliente ya tiene (billing, regla 3). El v1 pone "planes" en `other` sin distinguir un plan contratado de uno nuevo.

## Comparativa de prompts

Mismo modelo (`nvidia/nemotron-3.5-super-vl:free`), mismo dataset de 44 casos y temperature 0.

| Versión | Técnica | Qué agrega |
|---|---|---|
| `v1_zero_shot.yaml` | Zero-shot | Línea base: categorías en pocas palabras, catálogo de acciones y reglas de tono y de no prometer. |
| `v2_few_shot.yaml` | Few-shot | v1 más 8 ejemplos, 2 por categoría (uno claro y uno de frontera). Ninguno está en el dataset. |
| `v3_few_shot_reglas.yaml` | Few-shot con reglas | v2 más las definiciones de `evals/criterios_etiquetado.md`, cuatro reglas de desempate, reglas generales y un bloque de políticas: no promete reintegros, descuentos, plazos ni aprobaciones. |

Resultados de cada corrida completa:

| Métrica | v1 (1.ª) | v1 (2.ª) | v2 | v3 (1.ª) | v3 (2.ª) |
|---|---|---|---|---|---|
| Accuracy | 95,5 % | 97,7 % | 97,7 % | 100 % | 100 % |
| Macro-F1 | 0,954 | 0,977 | 0,977 | 1,000 | 1,000 |
| F1 `billing` | 0,909 | 0,957 | 0,957 | 1,000 | 1,000 |
| F1 `technical` | 0,952 | 0,952 | 0,952 | 1,000 | 1,000 |
| F1 `account` | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| F1 `other` | 0,957 | 1,000 | 1,000 | 1,000 | 1,000 |
| JSON válido al primer intento | 100 % | 100 % | 100 % | 100 % | 100 % |
| Tokens por ticket (entrada + salida) | 1.317 | 1.358 | 1.982 | 2.663 | 2.661 |
| Latencia p50 | 5,48 s | 6,31 s | 3,83 s | 3,64 s | 4,39 s |
| Costo por ticket a precio de lista | 0,000429 USD | 0,000449 USD | 0,000435 USD | 0,000548 USD | 0,000547 USD |
| Respuestas con promesas indebidas | no medido (*) | 0 % | 0 % | 0 % | 0 % |
| Casos fallados | t022, t033 | t022 | t022 | ninguno | ninguno |

(*) La primera corrida del v1 se hizo antes de guardar el `answer` en el reporte, así que su porcentaje de promesas no se puede recalcular. La segunda sí lo guarda.

**Ruido.** Dos corridas del mismo prompt v1 difieren en un caso (t033): macro-F1 de 0,954 a 0,977. Las dos corridas de v3 dan el mismo resultado, 44 de 44. Con 44 casos, un caso equivale a 2,3 puntos de accuracy, así que la resolución de la comparación es baja.

**Regla de elección.** Se aplicó en este orden:

1. **Macro-F1**, solo si la diferencia supera el ruido medido. v3 sube de 0,977 a 1,000 frente a la segunda corrida del v1. Esa diferencia es igual al ruido medido (un caso), así que **no lo supera de forma inequívoca**. Contra la primera corrida del v1 la diferencia es mayor, pero el criterio se aplicó contra el ruido. Se documenta así.
2. **Promesas indebidas**: 0 % en las tres versiones medidas. Empate.
3. **Casos corregidos**: t022 falló en las dos corridas del v1 y en v2. v3 lo acierta en sus dos corridas, y t033 también queda bien. v3 no introduce fallos nuevos y v2 no corrige t022. Por este criterio gana v3.
4. **Costo y latencia**: no desempatan, porque v3 ya gana en el paso 3. v3 usa casi el doble de tokens por ticket que v1 (2.661 contra 1.358) porque el system prompt y los ejemplos viajan en cada request. Su costo a precio de lista es un 22 % mayor por ticket que el de la segunda corrida de v1. La latencia varía entre corridas del mismo modelo, así que no se puede comparar con confianza.

**Qué se probó y qué falló.**

- **v2 no mejoró a v1 de forma repetible.** Tiene el mismo resultado que la segunda corrida del v1 y sigue fallando t022. Los ejemplos de frontera no alcanzaron para la multi-intención.
- **La hipótesis de v3 sobre promesas no se puede comprobar con este dataset.** El v1 ya tenía 0 % de promesas, así que la métrica no discrimina entre versiones.

**Chain-of-thought.** No se agregó como versión aparte. Los modelos gratuitos ya razonan antes de responder (cientos de tokens de razonamiento que no aparecen en la salida), y el contrato tiene solo cuatro campos. Un campo de razonamiento cambiaría el contrato que recibe el consumidor, así que el razonamiento queda dentro del modelo.

**Casos que siguen fallando.** Con v3, ninguno en las dos corridas. Con v1 y v2, t022.

**Limitaciones de la comparación.**

- **Circularidad.** Las reglas de v3 salen de `evals/criterios_etiquetado.md`, la definición con la que se etiquetó el dataset, y se escribieron después de ver los dos fallos del v1. Por eso el 100 % del dataset no es una estimación fuera de muestra. El holdout de abajo la contrasta con tickets nuevos.
- **Diferencia entre las reglas del prompt y los criterios.** Para una consulta que no encaja en ninguna regla, los criterios piden marcarla como ambigua y revisarla a mano. El prompt v3 pide elegir la categoría más cercana y bajar la confianza. El runner no mide esa diferencia, pero conviene saberla al leer la comparación.
- **Un solo modelo** en la comparación de prompts. Gemini y dots se midieron con v3 en la comparativa de modelos.
- **Detector de promesas.** Son patrones de expresiones regulares, probados offline con 22 casos positivos y 34 negativos. Falso positivo conocido: "te devolvemos la llamada". Falso negativo conocido: "a la brevedad" o "en breve", sin plazo concreto.

## Validación fuera de muestra (holdout)

`evals/holdout.jsonl` tiene 16 tickets (ids `h001` a `h016`, 4 por categoría) que no se usaron para escribir los prompts. Los armó un subagente de IA sin leer `prompts/`, con los criterios de `evals/criterios_etiquetado.md`, y el orquestador los revisó. Ninguno repite el dataset: la similitud máxima con sus 44 casos es 0,436 (`difflib.SequenceMatcher`). Incluye siete casos difíciles con la regla de desempate en `notes`, dos fuera de dominio, uno en inglés y uno muy corto.

| Métrica | v1 | v3 |
|---|---|---|
| Accuracy | 100 % (16 de 16) | 100 % (16 de 16) |
| Macro-F1 | 1,000 | 1,000 |
| Respaldos / promesas indebidas | 0 / 0 % | 0 / 0 % |
| Tokens por ticket (entrada + salida) | 1.414 | 2.738 |
| Costo por ticket a precio de lista | 0,000465 USD | 0,000573 USD |
| Latencia p50 / p95 | 5,85 s / 10,70 s | 4,82 s / 9,59 s |

Qué significa:

- **v3 no pierde accuracy con tickets nuevos.** Acierta los 16, igual que v1. Sus reglas no empeoran la clasificación de tickets que no se usaron para escribirlas.
- **El holdout no muestra que v3 sea mejor.** v1 también acierta todo, y con 16 casos un caso equivale a 6,25 puntos. La elección se apoya en t022, que está dentro del dataset.
- **Limitación compartida.** El holdout usa los mismos criterios que v3. Mide si las reglas se aplican bien a tickets nuevos, no si los criterios son los correctos. Ninguna etiqueta tuvo una segunda revisión independiente.
- **Costo.** v3 usa casi el doble de tokens por ticket y un 23 % más a precio de lista. A 400 tickets por día, la diferencia es de unos 0,04 USD por día.

## Comparativa de modelos y proveedores

Mismo prompt (v3), mismo dataset de 44 casos, guardrails activados y temperature 0. Nemotron es la corrida de 15:33, la misma configuración de la comparativa.

| Modelo | Proveedor | Accuracy | Macro-F1 | JSON válido al primer intento | Latencia p50 / p95 | Tokens por ticket | Costo real | Costo a precio de lista | Proyección mensual a 400 tickets por día (lista) |
|---|---|---|---|---|---|---|---|---|---|
| `nvidia/nemotron-3.5-super-vl:free` | OpenRouter | 100 % (44/44) | 1,000 | 100 % | 3,82 s / 18,65 s | 2.692 | 0 USD | 0,000551 USD por ticket | 6,61 USD |
| `gemini-3.5-flash-lite` | Gemini | 100 % (44/44) | 1,000 | 100 % | 1,18 s / 4,51 s | 2.183 | 0 USD | 0,000843 USD por ticket | 10,11 USD |
| `dots-studio/dots-3-note-preview:free` | OpenRouter | 100 % (44/44) | 1,000 | 97,7 % (1 caso con reintento) | 11,03 s / 20,72 s | 3.166 | 0 USD | 0,000788 USD por ticket | 9,46 USD |

Todas las F1 por categoría son 1,000. Las diferencias reales están en latencia, contrato y costo.

- **Dots tuvo un reintento de validación** (t003, una respuesta inválida que el reintento corrigió). Además escribió seis acciones con errores de tipeo fuera del catálogo: `gestionar_usuos_y_permisos` (4 casos), `actualizar_medio_de_pag` (1) y `actualizar_medio_de pago` (1). Esa corrida es anterior al guardrail `action_off_catalog`, que hoy descartaría esas acciones (ver [seguridad.md](seguridad.md)).
- **Gemini** completó los 44 casos sin respaldos y sin respuestas inválidas. Tuvo dos reintentos de transporte recuperados (t030 y t037).
- **Nemotron** no tuvo respuestas inválidas ni acciones fuera del catálogo. Su mediana es buena (3,82 s), pero el p95 de 18,65 s muestra que a veces tarda mucho más.

**Recomendación.** Para producción, `gemini-3.5-flash-lite` con el prompt v3, en el nivel pagado:

- **Calidad:** empata con los otros dos en este dataset (44 de 44). La decisión sale de latencia, contrato y costo.
- **Latencia:** es el más rápido, con p50 de 1,18 s y p95 de 4,51 s.
- **Contrato:** 44 de 44 válidos al primer intento y ninguna acción fuera del catálogo.
- **Costo:** 10,11 USD por mes a 400 tickets por día, a precio de lista. Son 3,50 USD por mes más que nemotron.

Condiciones y lo que no se sabe:

- El nivel gratuito de Gemini no publica límites para este modelo. En producción hay que pagar, y el costo real sería el de lista.
- Con 44 casos y un prompt diseñado sobre este dataset, la accuracy no discrimina. Antes de decidir por calidad hay que correr los tres modelos en el holdout. Hoy solo nemotron está corrido ahí.
- Nemotron es la alternativa si el costo pesa más que la latencia: es el más barato a precio de lista, con 100 % de accuracy, pero su p95 es de 18,65 s.
- Dots se descarta: es el más lento, el único que necesitó un reintento de validación y el que escribió acciones fuera del catálogo.

## Cómo se decide cada corrida en el dataset

Cada caso tiene una categoría esperada. Un caso es acierto si la categoría final coincide. La suite no compara acciones contra una lista exacta: mide qué porcentaje pertenece al catálogo, para no penalizar una redacción válida de la misma acción. Los ejemplos few-shot de v2 y v3 no están en el dataset ni se van a agregar: si un ejemplo fuera un caso del dataset, el modelo vería la respuesta antes de la prueba y el caso quedaría inflado.

Las etiquetas las redactó un subagente de IA según la especificación del proyecto, y el orquestador las revisó. Los tickets son sintéticos. No hubo una segunda revisión independiente. Ver [uso-de-ia.md](uso-de-ia.md).
