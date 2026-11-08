# Etapa: Parte 3, métricas

- **Rama:** `parte-03-metricas`, creada desde la punta de `parte-02-flujo-minimo`.
- **Explicación:** `_notas/03-metricas.md`.

Antes de empezar, leé completos `_notas/ESPEC.md`, `_notas/02-flujo-minimo.md` (lo que dejó la etapa anterior) y el código actual de `src/`.

## Objetivo

Cada request de triage agrega **una línea** a `data/metrics.jsonl` con los campos de la ESPEC §5 ("Métricas"). El costo tiene que ser **reproducible y auditable**: cualquiera puede recalcularlo desde los tokens y los precios versionados.

## Decisiones del orquestador sobre lo que reportó la Parte 2

- **Latencia:** `latency_s` en métricas es la latencia **total** del request de triage: tiempo de reloj desde que entra a `triage()` hasta que hay respuesta, incluidos los reintentos de transporte. Hoy `LLMResponse.latency_s` mide solo el intento exitoso. Medí el total en `triage()` con `time.perf_counter()` y exponelo en `TriageResult`.
- **El clone del README sigue por HTTPS**, a propósito: el corrector puede no tener SSH. No lo cambies.
- **No se tocan acá:** el tope de `Retry-After`, el reintento de parseo y el respaldo van en la Parte 4; el escape de `</ticket>`, en la Parte 8.

## Pasos y commits

1. **Precios en `config/models.yaml`.** Para cada modelo de OpenRouter configurado:
   - `price_in_per_mtok` y `price_out_per_mtok`: el precio real que se paga (0 en los `:free`).
   - `list_price`: `{model, in_per_mtok, out_per_mtok, source, date}` de un modelo pago de referencia.
   - **Precio de referencia:** la variante paga del mismo modelo (sin `:free`), tomada de `https://openrouter.ai/api/v1/models`. Es un GET público que no consume cuota; los precios vienen en USD por token, así que multiplicalos por 1e6. Si no existe la variante paga, elegí el modelo pago más parecido y explicá por qué. Fecha: la de hoy.
2. **`src/metrics.py`** (responsabilidad única: costo y registro):
   - `estimate_cost(prompt_tokens, completion_tokens, in_per_mtok, out_per_mtok) -> float`.
   - Una función que arme el registro a partir del resultado del triage.
   - `append_metrics(record, path)`: agrega una línea en UTF-8, crea la carpeta si no existe y nunca reescribe lo anterior.
   - `timestamp` en ISO 8601 con zona horaria UTC.
   - Si el proveedor reporta su costo (`reported_cost_usd`), guardalo también como `reported_cost_usd`. Así se puede contrastar con el costo calculado.
3. **Integración:**
   - La CLI registra con `source="cli"`. El runner futuro va a usar `source="eval"`, así que dejá la función lista para recibir el `source`.
   - El registro no debe meterse dentro de `triage()`: la CLI (y después el runner) llaman a `metrics` con el `TriageResult`. Así `triage` no depende del filesystem (SOLID-S/D).
   - **Los errores de escritura de métricas no rompen la CLI:** avisan por stderr y el JSON igual sale.
   - Los requests que fallan con `ProviderError` no generan línea, porque no hubo consumo. Dejalo documentado.
   - Commit: `feat(metrics): registra tokens, latencia y costo`
4. **Primeras ejecuciones registradas:**
   - Corré la CLI con 2 tickets reales.
   - Verificá que `data/metrics.jsonl` tenga 2 líneas válidas y que `cost_usd` y `cost_usd_list_price` coincidan con la fórmula. Mostrá la cuenta en tu reporte.
   - Commit: `chore(data): registra primeras ejecuciones`
5. **README:** agregar la sección "Métricas y costo" con:
   - una tabla `campo | pregunta que responde`, porque la guía pide que cada métrica responda una pregunta concreta;
   - la fórmula del costo y de dónde salen los precios (fuente y fecha);
   - un ejemplo de auditoría: una línea real de `metrics.jsonl` y la cuenta a mano;
   - una proyección a 400 tickets por día (costo real y a precio de lista).

   Quitá de "Pendiente" lo que ya está hecho.
   - Commit: `docs(readme): documenta métricas y costo`

## Verificación

- `git log --oneline parte-02-flujo-minimo..HEAD`: 3 commits con el formato correcto.
- `data/metrics.jsonl` está versionado; `.env` y `_notas/` no.
- La CLI sigue sacando solo JSON por stdout.

Al final escribí `_notas/03-metricas.md` (ESPEC §6), con un diagrama ASCII de dónde se mide cada cosa, y devolvé el reporte de la ESPEC §7.
