# Etapa: Parte 5, dataset de evaluación

- **Rama:** `parte-05-dataset`, creada desde la punta de `parte-04-robustez-gemini`.
- **Explicación:** `_notas/05-dataset.md`.

Antes de empezar, leé completos `_notas/ESPEC.md` y `_notas/00-consigna-y-analisis.md` (sección 1.2 y la parte de dataset de la Parte 2).

## Material ya hecho y revisado por el orquestador

Está en `<scratchpad>\dataset\`:
- `dataset.jsonl`: 44 tickets, 11 por categoría, con 9 casos de frontera documentados.
- `criterios_etiquetado.md`: definiciones, 4 reglas de desempate y reglas generales.
- `control_dataset.py`: script de control.
- `fewshot_candidatos.jsonl`: **no** va en esta etapa; es para la Parte 7.

Decisiones del orquestador sobre ese borrador:
- **No se agrega `expected_actions`.** El runner va a medir el porcentaje de acciones que pertenecen al catálogo, no una coincidencia exacta.
- **Se aceptan las reglas generales extra** de los criterios.
- **Las etiquetas quedan como están.**

## Pasos y commits

1. **Dataset:**
   - Copiá `dataset.jsonl` a `evals/dataset.jsonl` sin cambios, salvo que encuentres un error de formato: si es así, informalo.
   - Creá `evals/__init__.py` vacío, para que después funcione `python -m evals.runner`.
   - Commit: `feat(evals): agrega dataset de evaluación`
2. **Criterios:**
   - Copiá `criterios_etiquetado.md` a `evals/criterios_etiquetado.md`.
   - Commit: `docs(evals): agrega criterios de etiquetado`
3. **README:** sección "Dataset de evaluación" con:
   - tamaño y formato de cada línea;
   - una tabla de distribución por categoría y otra por tag (calculadas con un script, no a mano);
   - cómo se construyó y qué variedad cubre;
   - un link a los criterios;
   - la regla de que los ejemplos few-shot nunca están en el dataset, para no inflar las métricas.

   Actualizar "Pendiente".
   - Commit: `docs(readme): documenta el dataset de evaluación`

## Verificación

- Corré el script de control de nuevo sobre `evals/dataset.jsonl` (desde el scratchpad, no lo copies al repo) y mostrá el resultado.
- `git log --oneline parte-04-robustez-gemini..HEAD`: 3 commits. `git status` limpio.
- Esta etapa **no hace llamadas a APIs**.

Al final escribí `_notas/05-dataset.md` (ESPEC §6):
- por qué 44 casos balanceados y no más;
- por qué incluir casos difíciles;
- las reglas de desempate con un ejemplo cada una;
- qué riesgos tiene un dataset hecho por la misma persona que hace el prompt (sesgo) y cómo se mitigó.

Devolvé el reporte de la ESPEC §7.
