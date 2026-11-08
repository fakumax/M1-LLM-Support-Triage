# Tarea: holdout fuera de muestra (en paralelo a la Parte 8)

**No uses git ni llamadas a APIs. No toques el repo.** Escribí solo en:
`<scratchpad>\holdout\`

## Por qué existe

El prompt v3 se diseñó mirando los 44 tickets de `evals/dataset.jsonl`, y dio 100 %. Para saber si generaliza, hacen falta **tickets que el prompt nunca vio**.

**No leas ningún archivo de `prompts/`** ni las explicaciones de `_notas/` que hablan de los prompts (`07-prompts.md`). Vos sos un etiquetador independiente.

## Qué leer

- La consigna: `_notas/00-consigna-y-analisis.md`, sección 1.2 (tono de los tickets).
- **Las definiciones de negocio:** `evals/criterios_etiquetado.md`. Está en la rama `parte-07-prompts`; leélo con `git show parte-07-prompts:evals/criterios_etiquetado.md`, que es lectura y está permitida.
- **El dataset existente**, solo para **no repetir** ni parafrasear sus tickets: `git show parte-07-prompts:evals/dataset.jsonl`.

## Entregable: `holdout.jsonl`

**16 tickets nuevos, 4 por categoría.** Mismo formato que el dataset, con ids `h001` a `h016`:

```json
{"id": "h001", "query": "...", "expected_category": "billing", "tags": ["..."], "notes": "..."}
```

- **Que sean distintos del dataset:** otras situaciones de Nubbix, como inventario, sucursales, exportaciones, API, notificaciones, roles, cupones o facturación recurrente. Usá otros países y registros.
- **Al menos 6 casos difíciles** (multi-intención o frontera), con la regla de desempate aplicada en `notes`.
- **Al menos 1** fuera de dominio, **1** en otro idioma y **1** muy corto.
- **Sin ataques ni prompt injection:** el holdout mide clasificación, no seguridad.

## Control

Corré un script con `<repo>\.venv\Scripts\python.exe -I`, guardado en la carpeta del scratchpad, que verifique:
- que las 16 líneas son JSON válido;
- que los ids son únicos;
- que hay 4 por categoría;
- que la similitud con todos los tickets del dataset es menor a 0,6 (`difflib.SequenceMatcher`).

En tu reporte final incluí ese resultado y la lista de los casos difíciles con su regla.
