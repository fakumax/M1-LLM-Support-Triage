# Etapa: Parte 6, runner de evals

- **Rama:** `parte-06-runner-evals`, creada desde la punta de `parte-05-dataset`.
- **Explicación:** `_notas/06-runner-evals.md`.

Antes de empezar, leé completos `_notas/ESPEC.md`, las explicaciones `_notas/02` a `_notas/05`, el código de `src/` y `evals/dataset.jsonl`.

## Objetivo

Cumplir la consigna: *"runner ejecutable por comando (script simple, no framework de testing) con score global y por categoría"*. El reporte tiene que ser claro, porque la rúbrica evalúa la "claridad del reporte".

## Decisiones del orquestador después de la Parte 4

- La firma real es `triage(query, provider, prompt, max_parse_retries)` y devuelve un `TriageResult` plano (ver "Estado real del código" en la ESPEC). Leé `src/triage.py`, `src/metrics.py` y `src/main.py` antes de diseñar, y reusá cómo arma las dependencias y cómo registra las métricas la CLI. **Si hay lógica de armado repetida entre la CLI y el runner, extraéla a una función compartida en `src/`; no la copies.**
- **Los límites gratuitos de Gemini no están publicados.** El default de `--sleep` para Gemini es conservador (4,5 s, unos 13 RPM). Si aparece un 429, ya lo maneja el backoff.
- `data/metrics.jsonl` se versiona: cada corrida suma sus líneas con `source="eval"`.

## Diseño

- **Comando:**
  ```
  python -m evals.runner [--provider openrouter|gemini] [--model ID] [--prompt v1] [--limit N] [--sleep S]
  ```
  Los valores por defecto salen de `config/models.yaml`.
- **Dependencias:** arma proveedor y prompt una sola vez y llama a `triage()` por cada caso (inyección de dependencias). Registra cada request en `data/metrics.jsonl` con `source="eval"`, usando las funciones de `src/metrics.py`; no dupliques esa lógica.
- **Ritmo:** pausa entre requests (`--sleep`, con un default por proveedor configurable en `config/models.yaml`) para respetar los límites gratuitos. OpenRouter: ≥ 3,2 s. Gemini: según el límite por minuto documentado en la Parte 4.
- **Catálogo de acciones:** tiene que existir como constante única en `src/`, por ejemplo `ACTION_CATALOG` en `src/schema.py`. El prompt lo menciona y el runner lo usa. El contrato no cambia: `actions` sigue siendo `list[str]`.
- **Métricas:**
  - Globales: accuracy y macro-F1.
  - Por categoría: precision, recall, F1 y support.
  - Matriz de confusión 4×4 (esperada × predicha).
  - Contrato: % con JSON válido al primer intento, % que necesitó reintento y % de respaldos.
  - % de acciones dentro del catálogo.
  - Latencia: media, p50 y p95.
  - Tokens totales.
  - Costo total (real y a precio de lista), costo por ticket y proyección a 400 tickets por día.
  - Calculá todo con Python puro (sin sklearn ni pandas). Funciones chicas en un módulo aparte, por ejemplo `evals/scoring.py`, separadas de la ejecución (SOLID-S).
- **Salida:**
  - Resumen legible en consola.
  - Dos archivos en `evals/results/`:
    - `<YYYYmmdd-HHMM>_<provider>_<model-slug>_<prompt>.json`, con métricas y detalle por caso (id, esperada, predicha, confidence, attempts, fallback, latency_s, acciones fuera del catálogo);
    - un `.md` con el mismo nombre y las tablas.
  - Si un caso cae en el respaldo, cuenta como predicción `other` (es lo que devolvió el sistema) y además se informa aparte.
- **Errores:**
  - Un `ProviderError` no transitorio (401, por ejemplo) aborta la corrida con un mensaje claro.
  - Los errores transitorios ya los maneja `triage()`.

## Pasos y commits

1. **Runner:**
   - Implementar el runner y el scoring.
   - Probarlo primero con `--limit 3`.
   - Commit: `feat(evals): agrega runner de evaluación`
2. **Corrida base (línea base):**
   - `python -m evals.runner --prompt v1` con OpenRouter y su modelo por defecto, sobre los 44 casos. Son unos 44 requests; con `--sleep` tarda unos minutos, así que corrélo en segundo plano si tu herramienta lo permite.
   - Commit: `chore(evals): agrega resultados de la línea base` (incluye `evals/results/*` y las líneas nuevas de `data/metrics.jsonl`).
3. **README:** sección "Evals" con:
   - cómo correrlo;
   - qué mide cada métrica y por qué importa en este caso (por ejemplo: recall de billing bajo = cobros mal derivados);
   - la tabla de resultados de la línea base (global y por categoría), con un link al reporte.

   Actualizar "Pendiente".
   - Commit: `docs(readme): documenta la suite de evals`

## Verificación

- La corrida completa termina sin abortar. Si hay respaldos o errores, informalos con su causa.
- Verificá con 2 o 3 casos que las métricas por categoría cuadren con la matriz de confusión (cuenta a mano en el reporte).
- `git log --oneline parte-05-dataset..HEAD`: 3 commits. `git status` limpio.

Al final escribí `_notas/06-runner-evals.md` (ESPEC §6):
- un diagrama del runner;
- cómo leer la matriz de confusión con un ejemplo real de la corrida;
- qué casos falló el v1 y una hipótesis de por qué. Esto alimenta la Parte 7.

Devolvé el reporte de la ESPEC §7, **incluyendo la lista de casos fallados** (id, esperada, predicha, query recortada).
