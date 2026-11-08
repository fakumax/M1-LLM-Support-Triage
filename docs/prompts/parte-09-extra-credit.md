# Etapa: Parte 9, extra credits (caché MD5 + comparativa de modelos)

- **Rama:** `parte-09-extra-credit`, creada desde la punta de `parte-08-guardrails`.
- **Explicación:** `_notas/09-extra-credit.md`.

Antes de empezar, leé completos `_notas/ESPEC.md`, las explicaciones `_notas/02` a `_notas/08`, el código de `src/` y `evals/`, y la sección de evaluación de la consigna (`_notas/00-consigna-y-analisis.md` §1.4).

## Objetivo

La rúbrica exige **al menos un extra credit** entre FastAPI, caché con hash MD5, LLM-as-judge en runtime y comparativa de modelos. Se hacen dos:
- **caché MD5**, que además ahorra cuota en las evals;
- **comparativa de modelos y proveedores.**

## 0. Validación fuera de muestra (holdout), agregada por el orquestador

En la Parte 7, v3 dio 100 % en las dos corridas, pero sus reglas salen de los mismos criterios con los que se etiquetó el dataset y se escribieron después de ver fallar t022 y t033 (circularidad). Para contrastarlo:

- Un subagente aparte armó, **sin ver los prompts**, 16 tickets nuevos (4 por categoría), revisados por el orquestador. Están en `<scratchpad>\holdout\holdout.jsonl`. Copialo sin cambios a `evals/holdout.jsonl`.
- Agregá `--dataset <ruta>` al runner (por defecto `evals/dataset.jsonl`). El nombre del reporte tiene que indicar qué dataset se usó.
- Corré **v1 y v3** sobre el holdout con el modelo por defecto de OpenRouter: 32 requests.
- Commits:
  - `feat(evals): agrega holdout fuera de muestra`: el holdout y el flag `--dataset`;
  - `chore(evals): valida prompts en el holdout`: los resultados.
- README: en la sección de context engineering, agregá la tabla v1 vs v3 en el holdout y qué significa. **Si v3 baja en el holdout, se dice tal cual**: es información valiosa, no un fracaso.

## 1. Caché con hash MD5 (`src/cache.py`)

- **Patrón decorador:** `CachedProvider(LLMProvider)` envuelve cualquier proveedor y se comporta igual (SOLID-O/L).
  - La clave es el MD5 de un JSON canónico (`sort_keys=True`) con proveedor, modelo, system, messages, JSON Schema, temperature y max_tokens.
  - Se guarda en `data/cache/<md5>.json` con el texto y el uso de tokens.
  - Agregá `data/cache/` al `.gitignore`.
- **En un acierto de caché:** latencia ≈ 0 y no se llama a la API. En métricas se marca `cached: true`. El costo del request es 0, pero se conservan los tokens originales para poder auditar.
- **Flag `--cache`** en la CLI y en el runner, desactivado por defecto. En la CLI se usa poco; en el runner sirve para re-generar reportes sin gastar cuota.
- Commit: `feat(cache): cachea respuestas con hash md5`

## 2. Comparativa de modelos y proveedores

- Mismo prompt (el ganador de la Parte 7), mismo dataset y guardrails activados.
- **Modelos:**
  - `nvidia/nemotron-3.5-super-vl:free` (OpenRouter): la corrida de la Parte 8 sirve si es comparable; reusala.
  - `gemini-3.5-flash-lite` (Gemini).
  - **Un tercer modelo** gratis con salida estructurada. Candidatos: `dots-studio/dots-3-note-preview:free` (OpenRouter, unos 18 s por request) u otro flash de Gemini **si el nivel gratuito lo permite y responde en tiempo razonable**. Probalo con `--limit 2` antes; si tarda más de 60 s por request, descartalo y documentalo.
- **Cuota:**
  - Revisá los límites diarios de Gemini que documentó la Parte 4 antes de correr.
  - Si un modelo no completa los 44 casos por cuota, corré los que puedas con `--limit` y aclaralo en la tabla.
  - Para cada modelo, agregá su precio real y de lista a `config/models.yaml` (fuente + fecha).
- Commit: `chore(evals): compara modelos y proveedores`, con los resultados y las métricas.

## 3. README

Sección "Extra credits" con:
- **Caché:** cómo funciona, la clave MD5 y un ejemplo de corrida con y sin caché (tiempos reales).
- **Comparativa:** tabla con modelo | proveedor | accuracy | macro-F1 | F1 por categoría | % JSON válido | latencia p50/p95 | tokens por ticket | costo real | costo a precio de lista | proyección mensual a 400 tickets por día.
- **Recomendación** de qué modelo usar en producción y por qué, según calidad, latencia y costo. No hace falta que sea el más preciso: puede ser un compromiso, siempre explicado con números.

Commit: `docs(readme): documenta caché y comparativa`

## Verificación

- La caché funciona: correr dos veces el runner con `--cache --limit 3`. La segunda corrida tiene que dar 0 requests reales, latencia casi nula y las mismas predicciones. Mostrá los tiempos.
- `data/cache/` no aparece en `git status`.
- `git log --oneline parte-08-guardrails..HEAD`: commits con el formato correcto. `git status` limpio.

Al final escribí `_notas/09-extra-credit.md` (ESPEC §6) con:
- un diagrama del decorador de caché;
- por qué MD5 alcanza acá aunque no sirva para seguridad;
- cómo leer la tabla comparativa.

Devolvé el reporte de la ESPEC §7 con la tabla.
