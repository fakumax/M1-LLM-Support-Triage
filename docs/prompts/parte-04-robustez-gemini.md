# Etapa: Parte 4, robustez y segundo proveedor (Gemini)

- **Rama:** `parte-04-robustez-gemini`, creada desde la punta de `parte-03-metricas`.
- **Explicación:** `_notas/04-robustez-gemini.md`.

Antes de empezar, leé completos `_notas/ESPEC.md`, `_notas/02-flujo-minimo.md`, `_notas/03-metricas.md` y el código actual de `src/`.

## Objetivo

Cumplir dos requisitos de la consigna:
1. *"Reintento automático ante respuesta no parseable"* y *"la CLI no se cae ante un error transitorio"*.
2. *"≥2 proveedores configurables"*, con la misma abstracción y sin tocar `triage.py` para sumar el proveedor (SOLID-O).

## Datos ya verificados por el orquestador (08/11, google-genai 3.0.0)

- Esto funcionó:
  ```python
  client = genai.Client(api_key=...)
  r = client.models.generate_content(
      model="gemini-3.5-flash-lite",
      contents=...,
      config=types.GenerateContentConfig(
          temperature=0,
          response_mime_type="application/json",
          response_schema=<modelo Pydantic>,
      ),
  )
  ```
  - `r.text` trae el JSON.
  - `r.usage_metadata` tiene `prompt_token_count`, `candidates_token_count` y `thoughts_token_count` (este último puede ser `None`).
- **`gemini-3.5-flash-lite`:** 2 s y JSON válido. Es el modelo por defecto de Gemini.
- **`gemini-3.8-flash`:** tardó 182 s en el nivel gratuito. No lo uses como default.
- **Hallazgo:** flash-lite le **prometió un reembolso** al cliente ("ya estamos procesando el reembolso"). No lo arregles acá: lo atacan el prompt (Parte 7) y el guardrail de salida (Parte 8). Mencionalo en la explicación como evidencia de por qué validar el contenido.

## Decisiones del orquestador sobre lo que reportó la Parte 3

- **`timeout_s` pasa a 120** en `config/models.yaml`. En la Parte 3 un ticket tardó 39 s con un timeout de 60: no hay margen. Documentá el cambio en la tabla de parámetros del README.
- **Con el respaldo, `triage()` siempre devuelve un `TriageResult`**, salvo un `ProviderError` no transitorio. Así **todo request que consumió tokens genera su línea de métricas**, incluidos los que terminan en respaldo. Se cierra el hueco que dejó la Parte 3.
- **Se mantiene la estructura de precios** que creó la Parte 3: `providers.<p>.models.<id>` con `price_in_per_mtok`, `price_out_per_mtok`, `price_source`, `price_date` y `list_price{model, in_per_mtok, out_per_mtok, source, date}`. Gemini usa la misma.
- **Cupo de OpenRouter**, verificado por el orquestador en la documentación oficial (https://openrouter.ai/docs/api/reference/limits):
  - los modelos `:free` permiten 20 requests/minuto;
  - por día, 50 si la cuenta compró menos de USD 10 en créditos, y 1.000 si compró 10 o más (esta cuenta ya tiene más de 10);
  - pasarse del cupo devuelve 429.

  Actualizá el README con esa fuente y sacá el "pendiente de confirmar".
- **`--model` no se restringe a `:free` en el código.** La key tiene un tope de gasto de USD 0, así que un modelo pago falla con un error claro. Está bien así.

## Pasos y commits

1. **Reintento por salida inválida y respaldo** (en `src/triage.py` o en un módulo chico de parseo):
   - Extracción tolerante del JSON (ESPEC §5): sacar los cercos de código y tomar el primer objeto `{...}`.
   - Hasta `max_parse_retries` reintentos. En cada uno se agregan la salida mala como `assistant` y un `user` con el error de validación resumido.
   - Si se agotan los reintentos de parseo o los errores transitorios del proveedor, se devuelve el **contrato de respaldo** de la ESPEC con `fallback=True`. La CLI imprime ese JSON y sale con código 0.
   - Un `ProviderError` no transitorio (401, falta la key) sigue saliendo con código 1 y un mensaje claro.
   - `TriageResult` expone `attempts`, `fallback`, los tokens sumados de todos los intentos y la latencia total, para las métricas.
   - Commit: `feat(triage): reintenta ante salida inválida`
2. **Tope a `Retry-After`:**
   - La espera queda en `min(retry_after, max_retry_after_s)`, con `max_retry_after_s: 30` en `config/models.yaml`.
   - Sin tope, un 429 con una espera larga deja la CLI colgada.
   - Commit: `feat(providers): acota la espera de retry-after`
3. **Proveedor Gemini** en `src/providers/gemini.py`, registrado en `PROVIDERS`:
   - `system_instruction` = system. Los roles se mapean `user` → `user` y `assistant` → `model`.
   - El JSON Schema del contrato va como `response_schema` o `response_json_schema`, lo que acepte la versión instalada.
   - Desactivá los reintentos internos del SDK, si los tiene, y aplicá el timeout de la config.
   - Errores: 429 y 5xx → `TransientProviderError` (con `Retry-After` si viene); 4xx → `ProviderError`. Nunca dejes pasar excepciones del SDK (SOLID-L).
   - `completion_tokens` = `candidates_token_count` + `thoughts_token_count`, porque el razonamiento se cobra como salida.
   - **`config/models.yaml`:**
     - Proveedor `gemini` con `api_key_env: GEMINI_API_KEY` y `default_model: gemini-3.5-flash-lite`.
     - Precio real 0 (nivel gratuito).
     - `list_price` = precio del nivel pago de ese modelo según la página oficial de precios de Gemini API (fuente + fecha). Si no lo encontrás, usá el flash-lite pago más cercano y explicalo.
   - **Límites del nivel gratuito** (requests por minuto y por día del modelo elegido): buscalos en la documentación oficial y anotalos en el README. El runner los va a necesitar.
   - Commit: `feat(providers): agrega proveedor de gemini`
4. **Ejecuciones reales:**
   - 2 tickets con `--provider gemini` y 1 con OpenRouter, para chequear que nada se rompió.
   - `data/metrics.jsonl` suma esas líneas.
   - Commit: `chore(data): registra ejecuciones con gemini`
5. **README:**
   - Tabla de proveedores (proveedor, SDK, modelo por defecto, límites gratuitos).
   - Ejemplo real con `--provider gemini`.
   - Sección "Robustez" con un diagrama ASCII del ciclo intento → validación → reintento → respaldo, y la tabla de qué error se reintenta y cuál no.
   - Actualizar "Pendiente".
   - Commit: `docs(readme): documenta reintentos y gemini`

## Verificación (obligatoria)

- **Sin gastar cuota:** probá con un proveedor falso en memoria (un script en el scratchpad o en `_notas/`, **no se commitea**):
  - una salida inválida y después una válida → `attempts=2` y respuesta correcta;
  - siempre inválida → respaldo con `fallback=True`;
  - `TransientProviderError` siempre → respaldo, sin traceback.

  Mostrá las salidas en tu reporte.
- Llamadas reales: las del paso 4.
- `git log --oneline parte-03-metricas..HEAD`: commits con el formato correcto. `git status` limpio.

Al final escribí `_notas/04-robustez-gemini.md` (ESPEC §6). Incluí el diagrama del ciclo de reintento y dónde se ven SOLID-O y SOLID-L (agregar Gemini sin tocar `triage.py`). Devolvé el reporte de la ESPEC §7.
