# Uso de IA en el proyecto

La consigna pide documentar los prompts usados con IA y explicar cómo influyeron en las decisiones técnicas. Este documento resume, por etapa, el objetivo y las instrucciones clave de cada prompt, y qué decisiones influyó. El texto completo de las instrucciones de cada etapa está en [docs/prompts/](prompts/README.md), con el modelo que ejecutó cada una.

## Herramientas

- **Claude Code como orquestador** (Claude Opus 5.5). Diseñó la arquitectura, escribió la especificación técnica común y las instrucciones de cada etapa, y revisó cada etapa. Tomó las decisiones técnicas dentro del alcance, los proveedores y las reglas que fijó el humano. El humano revisa y aprueba la entrega.
- **Subagentes Claude Haiku 5.5** (esfuerzo extra-high), uno por etapa, para implementar. Algunas tareas separadas los usaron para redactar el borrador del dataset y el holdout.
- **Revisión final de cada rama** con Claude Opus 5.5: cinco revisores, en solo lectura, revisaron las diez ramas.
- **Modelos del producto**: `nvidia/nemotron-3.5-super-vl:free` y `dots-studio/dots-3-note-preview:free` por OpenRouter, y `gemini-3.5-flash-lite` por Gemini. Son los modelos que el servicio llama y que se evalúan. No se usaron para programar, y el repo no usa un LLM como juez: las promesas indebidas se detectan con reglas.

## Cómo se trabajó

- Una rama por etapa, creada desde la punta de la anterior (`parte-02-flujo-minimo` a `parte-13-readme`). Los subagentes nunca hicieron push. El orquestador subió el commit inicial y, con autorización del humano, la entrega.
- Reglas comunes para todos los agentes, fijadas en la especificación: Conventional Commits en español, en minúscula y de 50 caracteres como máximo; sin atribución a IA en los mensajes de commit; sin `git push`; `.env`, notas y `data/cache/` fuera de Git; código sin comentarios; SOLID aplicado de forma concreta; runner sin frameworks de testing; stdout de la CLI solo con JSON; README solo con lo que funciona.
- Cada etapa terminó con una explicación local: decisiones con su alternativa descartada, pruebas con salida real y preguntas de checkpoint.
- Las llamadas a APIs se minimizaron. Cada request real quedó en `data/metrics.jsonl`.

## Prompts por etapa

### Etapa 1: setup y análisis de la consigna (partes 0 y 1)

- **Objetivo del prompt:** transcribir y analizar la consigna, armar el plan por partes hacia la entrega y generar los archivos de setup.
- **Instrucciones clave:** la consigna es la fuente de verdad; versiones de dependencias fijadas con `==`; `.env.example` con nombres de variables y sin valores; notas fuera del repo.
- **Decisiones que influyó:** `requirements.txt` con versiones fijas; `.env.example` sin credenciales; `.gitignore` con `.env`, `.venv/`, `__pycache__/` y `_notas/`; no crear carpetas vacías; README del clon por HTTPS para el corrector.

### Etapa 2: flujo mínimo

- **Objetivo del prompt:** una CLI de punta a punta con OpenRouter y el prompt v1. Sin reintentos, métricas ni Gemini todavía.
- **Instrucciones clave:** quitar `anthropic`; contrato `SupportResponse` tal como está en la especificación; configuración en YAML; proveedor detrás de `complete()`; probar `reasoning.effort=low` y dejarlo solo si ayuda; prompt v1 con tono amable, no prometer y ticket tratado como dato; `triage()` recibe sus dependencias; stdout solo JSON.
- **Decisiones que influyó:** salida con `response_format` `json_schema` estricto, generado desde el modelo Pydantic; `max_retries=0` en el SDK; no usar `reasoning.effort=low` (en una prueba previa con una muestra por variante, la diferencia de latencia quedó dentro del ruido y generó más tokens de salida); excepciones propias del proyecto para que los proveedores sean intercambiables; `PROVIDERS` como diccionario; `load_env()` explícito.

### Etapa 3: métricas y costo

- **Objetivo del prompt:** una línea por request en `data/metrics.jsonl`, con un costo reproducible y auditable.
- **Instrucciones clave:** precios en `config/models.yaml` con fuente y fecha; latencia total medida dentro de `triage()`; el registro lo escribe la CLI y no `triage()`; un error de escritura no tumba la CLI; README con una tabla de campo a pregunta y una auditoría a mano.
- **Decisiones que influyó:** `attempts` lo reporta el proveedor; precio de lista de nemotron como referencia de la variante paga; redondeo a 8 decimales; `reported_cost_usd` en el registro para contrastar.

### Etapa 4: robustez y segundo proveedor

- **Objetivo del prompt:** reintento ante salida inválida, una CLI que no se cae ante errores transitorios y un segundo proveedor sin tocar `triage()`.
- **Instrucciones clave:** extracción tolerante del primer objeto JSON; hasta `max_parse_retries` reintentos con la salida mala y el error como turnos; respaldo con `fallback=true`; tope a `Retry-After`; Gemini con los reintentos del SDK desactivados; `completion_tokens` incluye el razonamiento; timeout de 120 s; límites gratuitos verificados en la documentación oficial.
- **Hallazgos que llegaron a la etapa:** en una prueba previa, `gemini-3.8-flash` tardó 182 s, y `gemini-3.5-flash-lite`, 2 s. Flash-lite le prometió un reembolso a un cliente en una prueba.
- **Decisiones que influyó:** `min(retry_after, 30)`; `gemini-3.5-flash-lite` como default; `timeout_s` de 120; el respaldo es un resultado y no una excepción; `httpx2` fijado porque el proveedor lo importa directamente.

### Etapa 5: dataset y criterios de etiquetado

- **Objetivo del prompt:** incorporar el dataset borrador sin cambios, los criterios de etiquetado y el paquete `evals` para el runner. Sin llamadas a APIs.
- **Instrucciones del borrador (tarea de un subagente):** 44 tickets con 11 por categoría, con variedad de registro, errores de tipeo, mayúsculas, mensajes muy cortos y largos, enojos, multi-intención, ambigüedad, fuera de dominio y otro idioma; al menos 8 casos difíciles con la regla de desempate en `notes`; criterios en unas 40 líneas con cuatro reglas de desempate; ejemplos few-shot separados del dataset; un script de control.
- **Decisiones que influyó:** sin `expected_actions` (se mide si la acción pertenece al catálogo); nueve casos difíciles; tickets sintéticos, sin datos de personas reales; few-shot fuera del dataset para no inflar las métricas; sesgo declarado porque quien etiqueta es quien escribe el prompt.

### Etapa 6: runner de evals

- **Objetivo del prompt:** un runner ejecutable por comando, sin frameworks, con score global y por categoría.
- **Instrucciones clave:** si la CLI y el runner arman lo mismo, extraer una función compartida; métricas en Python puro en un módulo aparte; accuracy, macro-F1, precision, recall, F1, matriz, contrato, catálogo, calibración, latencia y costo; reportes `.json` y `.md`; un respaldo cuenta como `other` y se informa aparte; un error no transitorio aborta la corrida.
- **Decisiones que influyó:** `src/pipeline.py` compartido por la CLI y el runner; percentiles por rango más cercano; `--limit` no guarda reportes, para que `evals/results/` tenga solo corridas comparables; el runner exige `:free` en OpenRouter; la pausa por proveedor vive en `config/models.yaml`.

### Etapa 7: versiones de prompt y elección con datos

- **Objetivo del prompt:** escribir v2 y v3, medir el ruido y elegir con una regla fijada antes de ver los resultados.
- **Instrucciones clave:** repetir v1 para medir el ruido; métrica de promesas indebidas con patrones en `src/policy.py`, probada offline; regla de elección en orden (macro-F1 solo si supera el ruido, después promesas, después casos corregidos sin fallos nuevos, después costo y latencia); ejemplos en tuteo; documentar la circularidad; el chain-of-thought no va como versión aparte.
- **Decisiones que influyó:** v3 como default. La elección se documentó con honestidad: el macro-F1 no supera el ruido de forma inequívoca, y el desempate lo dio que v3 corrige t022. No se corrió Gemini en esta etapa, porque sus límites no estaban publicados.

### Etapa 8: guardrails de entrada y salida

- **Objetivo del prompt:** al menos un guardrail de entrada y uno de salida, en capas. Sin endpoint de moderación de OpenAI, porque no hay key.
- **Instrucciones clave:** entrada: validación de largo, patrones de injection en español, inglés y portugués, marcadores de rol, delimitador, base64 y enmascarado de tarjetas con Luhn; bloqueo solo para riesgo alto; neutralizar para riesgo medio y bajo; salida: canary, fuga por fragmentos del system prompt, promesas reusando `find_promises` y ofensivos; un cliente enojado no se bloquea; flag `--no-guardrails`.
- **Decisiones que influyó:** el riesgo alto bloquea sin llamar al modelo; el canary se agrega al armar el system prompt, sin tocar los YAML de prompts; umbral de 12 palabras para la fuga; corrección de dos falsos positivos (la frase "te devolvemos la llamada" y la regla de odio con "deberían morir"). Ninguna regla se disparó en los 44 tickets legítimos.

### Etapa 9: holdout, caché y comparativa de modelos

- **Objetivo del prompt:** validar con tickets nuevos, agregar una caché y comparar modelos.
- **Instrucciones clave:** un subagente escribe 16 tickets sin leer `prompts/`, con controles de JSON válido, ids únicos, cuatro por categoría y similitud menor a 0,6 con el dataset; la caché es un decorador del proveedor con clave MD5 de un JSON canónico; un tercer modelo se descarta si tarda más de 60 s por request; la recomendación se justifica con números.
- **Decisiones que influyó:** el runner recibe `--dataset`; la caché no toca `triage()`; la pausa se espera solo después de una llamada real; el precio de lista de dots es una aproximación con nemotron; el holdout no decide entre v1 y v3, solo muestra que v3 no empeora.

### Etapa 10: bonus de resistencia adversarial

- **Objetivo del prompt:** una suite de 10 ataques con variantes triviales, medida con y sin guardrails.
- **Instrucciones clave:** los criterios de éxito se evalúan en código; cada ataque registra qué capa lo frenó; reusar el scoring y el runner; no usar caché en la suite; un guardrail nuevo descarta las acciones fuera del catálogo con el código `action_off_catalog`, porque la comparativa mostró acciones con typos; el mensaje de commit no pasa de 50 caracteres.
- **Decisiones que influyó:** el éxito se mide sobre la respuesta final del usuario; la etiqueta de capa `prompt (entrada sin bloqueo)`; no corregir el hueco de `< /ticket >`, porque ningún ataque pasó con los guardrails activados. El hueco se cerró en la revisión final (etapa 12A).

### Etapa 11: cierre

- **Objetivo del prompt:** README final de 350 a 450 líneas con el detalle en `docs/`, este documento, una ejecución limpia desde un clon y controles finales.
- **Instrucciones clave:** cada número sale de `evals/results/` o de `data/metrics.jsonl`; sacar lo que ya está resuelto de "Pendiente"; ningún enlace interno roto; ninguna credencial en el repo ni en el historial.

### Etapa 12: revisión final (12A y 12B)

- **Objetivo del prompt:** la 12A corrige el código según las observaciones de cinco revisiones Opus. La 12B corrige la seguridad de autolesión, los tags del dataset, la documentación y las notas, y deja la explicación de la revisión.
- **Instrucciones clave:** verificar la evidencia antes de cambiar nada; validar cada cambio de guardrails sin llamar a la API contra el dataset, el holdout y la suite adversarial; re-correr la suite adversarial real, y no el dataset si ninguna decisión cambia; cada número sale de `evals/results/`, `data/metrics.jsonl`, `config/models.yaml` o del reporte de la 12A; las únicas llamadas reales de la 12B son las tres del clon limpio.
- **Decisiones que influyó:** el detector de promesas pasó a listas con nombre y casos versionados; los tags tienen definiciones con umbrales, y `frontera` reemplaza a `ambiguo`; la autolesión de terceros se detecta por verbos y no por el sustantivo; la documentación declara lo que la revisión no corrigió.

### Etapa 13: README más corto

- **Objetivo del prompt:** reescribir el README de 427 líneas como puerta de entrada (instalar, configurar, ejecutar y entender las decisiones) y mover el detalle a `docs/`, sin perder datos ni cifras.
- **Instrucciones clave:** las 12 exigencias de la consigna siguen en el README; la tabla de módulos, el árbol de carpetas y el SOLID detallado van a `docs/arquitectura.md`; la tabla completa de decisiones y la lista completa de limitaciones, a `docs/decisiones-y-limitaciones.md`; ningún número nuevo; cada viñeta de la revisión final se verifica antes de salir del README; enlaces relativos comprobados con un script y sin anclas; ninguna llamada a APIs.
- **Decisiones que influyó:** el README queda como puerta de entrada y el detalle vive en `docs/`, sin perder datos. Las viñetas de la revisión final que no estaban en ningún doc de referencia se agregaron a `docs/seguridad.md`, `docs/evals.md` o esta página.

## Decisiones que salieron de experimentos guiados por IA

1. **Proveedores.** No había API de OpenAI ni de Anthropic, solo suscripciones. Se eligieron OpenRouter (modelos gratuitos, con la cuenta en el nivel de 1.000 requests por día) y Gemini (nivel gratuito de AI Studio). OpenCode Go se descartó porque sus condiciones limitan el uso a agentes de código.
2. **Modelos gratuitos que razonan.** Razonan entre 400 y 1.500 tokens antes de responder. Con `max_tokens` bajo, el JSON llegaba cortado, así que el default es 2000. Un modelo devolvió solo espacios en blanco y otro un JSON cortado: de ahí la validación con Pydantic y los reintentos.
3. **`reasoning.effort=low`.** Se midió en la etapa 2 y no se adoptó: la diferencia de latencia quedó dentro del ruido y generó más tokens de salida.
4. **Gemini 3.8 Flash contra 3.5 Flash-Lite.** El primero tardó 182 s en el nivel gratuito, en una prueba previa, y el segundo, 2 s. Flash-Lite quedó por defecto. Además prometió un reembolso: de ahí las políticas del prompt v3, la métrica de promesas y el guardrail de salida.
5. **Timeout de 120 s.** Un ticket tardó 39,2 s con un timeout de 60 s. No había margen.
6. **Elección del prompt por macro-F1 y con una regla escrita de antemano.** v1 ya daba 95,5 %, así que el margen para mejorar era de uno o dos casos. Se repitió v1 para medir el ruido: un caso equivale a 2,3 puntos. La regla quedó en este orden: macro-F1 solo si supera el ruido, promesas indebidas, casos corregidos sin fallos nuevos y costo. v3 ganó por el tercer criterio, porque acierta t022. El primer criterio no se superó de forma inequívoca, y así se documenta.
7. **Circularidad.** Las reglas de v3 son los criterios con los que se etiquetó el dataset. Un holdout de 16 tickets, escritos por un subagente sin ver los prompts, dio 100 % con v1 y con v3. v3 no empeora, pero no queda demostrado que sea mejor.
8. **Guardrails por capas con cero falsos positivos en el dataset.** Ninguna regla se disparó en los 44 tickets legítimos. Un cliente enojado no se bloquea: t009, t022 y t027 pasan sin reglas. Hubo dos ajustes, uno de la frase "te devolvemos la llamada" y otro de las reglas de odio y DAN.
9. **Comparativa de modelos.** Los tres dieron 44 de 44, así que el dataset no los separa. Gemini flash-lite fue el más rápido y quedó como recomendación para producción en el nivel pagado. Dots escribió acciones con errores de tipeo, y de ahí nació el guardrail `action_off_catalog`.
10. **Caché MD5 como decorador del proveedor.** Sirve para repetir las evals sin gastar cuota. Se implementó como decorador de `LLMProvider`, así `triage()` no cambia. No se usó SQLite.
11. **Historia de Git limpia.** Los commits de corrección de estilo (el largo de una línea de `gemini.py`, las reglas de odio y DAN, y un fixup de la etapa 10) se fusionaron con `--fixup` y `--autosquash` en el commit de origen. La historia final no tiene commits `style:` ni de arreglo de un commit anterior. Queda un `fix(policy)` que corrige un falso positivo: es un cambio funcional.

## Qué decidió el humano

- El alcance del proyecto y avanzar por partes, con una rama por etapa.
- Los proveedores: OpenRouter y Gemini, ambos con nivel gratuito.
- Conventional Commits en español, sin atribución a IA en los commits y sin push automático.
- Código sin comentarios y SOLID aplicado con pragmatismo.
- Python 3.12.16.
- La revisión final de cada rama con Opus 5.5.

## Límites del uso de IA

- **Etiquetas.** El borrador del dataset y el holdout los redactó un subagente de IA. El orquestador los revisó, pero no hubo una segunda revisión humana independiente. Es el sesgo principal que el proyecto declara.
- **Verificación.** Las salidas de IA se contrastaron con pruebas offline (proveedores falsos y reglas con casos que deben disparar y casos que no), con la salida real de las corridas y con scripts de control, fuera del repo, que comparan los números del README con `evals/results/` y `data/metrics.jsonl`.
- **Modelos de terceros.** Los modelos del servicio son LLMs externos. El repositorio no los usa para juzgar sus propias respuestas.
