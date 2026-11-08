# Etapa: Parte 7, versiones de prompt y elección con datos

- **Rama:** `parte-07-prompts`, creada desde la punta de `parte-06-runner-evals`.
- **Explicación:** `_notas/07-prompts.md`.

Antes de empezar, leé completos:
- `_notas/ESPEC.md`;
- `_notas/06-runner-evals.md`, que trae los casos que falló el v1;
- el último reporte de `evals/results/`;
- `prompts/v1_zero_shot.yaml`;
- `evals/criterios_etiquetado.md`;
- la Parte 1 de `_notas/00-consigna-y-analisis.md`.

## Objetivo

La consigna pide *"al menos 2 versiones de prompt, documentadas y comparadas contra el dataset"* y una *"técnica de context engineering justificada con resultados, no con opiniones"*. La rúbrica evalúa el versionado, la comparativa empírica y la selección respaldada por datos.

## Situación después de la Parte 6 (decisiones del orquestador)

La línea base del v1 con `nvidia/nemotron-3.5-super-vl:free` dio **accuracy 95,5 % (42/44) y macro-F1 0,954**. Falló solo en dos casos:
- **t022:** multi-intención; se esperaba technical y predijo billing (regla 1);
- **t033:** precio del plan contratado; se esperaba billing y predijo other (regla 3).

**Hay efecto techo:** entre versiones, la diferencia en categoría va a ser de 1 o 2 casos y puede ser ruido. Para que la elección se apoye en datos:

1. **Medir el ruido:** corré el **v1 una segunda vez**, con el mismo modelo y los 44 casos. La diferencia entre las dos corridas del v1 es el ruido de referencia. Cuota usada hasta ahora: menos de 100 de 1.000 diarios, así que alcanza.
2. **Métrica de promesas indebidas** (nueva):
   - Creá `src/policy.py` con `find_promises(answer: str) -> list[str]`: patrones en español, inglés y portugués de reintegros, reembolsos, devoluciones, descuentos, bonificaciones o plazos prometidos **como hechos o compromisos**. Ejemplos: "ya estamos procesando el reembolso", "te vamos a devolver", "te aplicamos un descuento", "en 24 horas se acredita".
   - **No** son promesas: "un agente va a revisar si corresponde un reintegro" ni "evaluaremos tu caso".
   - Sumá al scoring y al reporte la métrica "% de respuestas con promesas indebidas", con los ids.
   - El guardrail de salida de la Parte 8 va a **reusar** esta función (DRY).
   - Probala offline con casos positivos y negativos antes de usarla.
   - Commit, antes de los prompts: `feat(evals): mide promesas indebidas en respuestas`.
   - Re-generá la métrica de la línea base v1 **desde su JSON guardado** (los `answer` están en el detalle por caso, o en `data/metrics.jsonl` si no). Si el JSON no guarda el `answer`, agregalo al reporte por caso y usá la segunda corrida del v1 como medición.
3. **Regla de elección**, en este orden:
   1. macro-F1, solo si la diferencia **supera el ruido medido**;
   2. si no, el % de promesas indebidas (menos es mejor);
   3. después, que corrija t022 o t033 sin introducir fallos nuevos;
   4. por último, tokens por ticket (costo) y latencia.

   Documentá con honestidad si la diferencia en categoría está dentro del ruido.
4. **Opcional:** corré solo el v1 y la ganadora con Gemini `gemini-3.5-flash-lite` (88 requests como máximo, `--sleep` por defecto) para ver si la mejora se sostiene en otro modelo. Si aparecen 429 persistentes o la cuota no alcanza, cortá y documentalo; no es obligatorio.

## Material disponible

`<scratchpad>\dataset\fewshot_candidatos.jsonl` tiene 8 ejemplos, 2 por categoría (uno claro y uno de frontera). Ninguno está en el dataset: el orquestador ya lo verificó.

**Decisión del orquestador:** las respuestas (`answer`) de los ejemplos tienen que estar en **español neutro con tuteo** ("podrías", "tu cuenta"), sin voseo. Nubbix atiende a toda LATAM, y el v1 ya responde con tuteo. Ajustalas al copiarlas.

## Versiones

- **v2, `v2_few_shot.yaml`:**
  - Parte de v1 y agrega los 8 ejemplos (`examples`). `src/prompts.py` ya los convierte en mensajes `user` / `assistant`.
  - Hipótesis: los ejemplos de frontera mejoran la separación entre categorías parecidas.
- **v3, `v3_few_shot_reglas.yaml`:**
  - v2 más las **reglas de desempate** y las definiciones precisas de `evals/criterios_etiquetado.md`, escritas como instrucciones para el modelo.
  - Más un bloque corto de **políticas de Nubbix**: qué puede decir y qué no el asistente N1. Nunca promete reintegros, descuentos, plazos ni excepciones; solo indica que un agente lo revisa.
  - Hipótesis: mejora los casos multi-intención y de frontera, y reduce las promesas indebidas. En la Parte 4 se vio que Gemini flash-lite prometió un reembolso.

**Riesgo a documentar:** v3 usa las mismas reglas con las que se etiquetó el dataset. Eso es legítimo, porque son la definición de negocio de cada categoría, pero puede inflar el resultado frente a tickets reales. Mencionalo como limitación.

**Chain-of-thought explícito:** no se agrega como versión aparte. Los modelos gratis ya razonan internamente antes de responder (cientos de tokens de razonamiento) y el contrato no tiene campo para el razonamiento. Explicá esta decisión en la explicación de la etapa y en el README.

## Pasos y commits

1. **v2:**
   - Agregar el archivo y probarlo con `--limit 3`.
   - Commit: `feat(prompts): agrega prompt v2 few-shot`
2. **v3:**
   - Agregar el archivo y probarlo con `--limit 3`.
   - Commit: `feat(prompts): agrega prompt v3 con reglas`
3. **Corridas completas:**
   - v2 y v3 con el **mismo proveedor y modelo** que la línea base del v1, sobre los 44 casos. Son unos 88 requests: respetá el `--sleep`.
   - Si los límites lo permiten y alguna diferencia es chica (menos de 3 puntos), repetí la versión dudosa una vez para ver la variación. Si no alcanza la cuota, decilo.
   - Commit: `chore(evals): compara versiones de prompt`, con los resultados y las líneas de métricas.
4. **Elección:**
   - Métrica principal: **macro-F1**.
   - Desempate: F1 de la peor categoría, después tokens por ticket y después latencia.
   - Poné la ganadora en `defaults.prompt_version` de `config/models.yaml`.
   - Commit: `feat(config): usa el prompt <vN> por defecto`. Si la ganadora es v1, no hay commit y lo justificás.
5. **README:** sección "Context engineering y elección del prompt" con:
   - una tabla comparativa v1 | v2 | v3: accuracy, macro-F1, F1 por categoría, % JSON válido al primer intento, tokens por ticket, latencia p50 y costo a precio de lista;
   - qué se probó, qué falló, por qué ganó la elegida (con los números) y los casos que siguen fallando.
   - Commit: `docs(readme): documenta la comparativa de prompts`

## Verificación

- Los 3 reportes usan el mismo modelo y el mismo dataset.
- `git log --oneline parte-06-runner-evals..HEAD`: commits con el formato correcto. `git status` limpio.

Al final escribí `_notas/07-prompts.md` (ESPEC §6):
- qué es zero-shot y qué es few-shot, con un diagrama de cómo se arman los mensajes;
- por qué ganó la versión elegida y qué significaría si no hubiera ganado.

Devolvé el reporte de la ESPEC §7 con la tabla comparativa y los casos que siguen fallando con la versión ganadora.
