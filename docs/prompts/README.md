# Prompts usados en el proyecto

Estas son las instrucciones que se usaron para producir el proyecto. `ESPEC.md` es la especificación común, el prompt base que leyó cada subagente. Los demás archivos son los encargos de cada etapa, y los dos borradores del dataset y del holdout. Las rutas del equipo se reemplazaron por `<repo>`, `<scratchpad>` y `<usuario>`. Estas copias son de referencia: el código y los prompts que usa la CLI son los de `src/` y `prompts/`.

## Orden de uso

1. `ESPEC.md`: reglas, arquitectura, contrato y reglas de git. Se leyó antes de cada etapa.
2. `borrador-dataset.md` (etapa 5) y `borrador-holdout.md` (etapa 9): tareas separadas de un subagente que redactó los tickets. El orquestador los revisó.
3. Etapas, en orden: `parte-02-flujo-minimo.md` a `parte-11-cierre.md`. Cada una tiene la rama, el alcance, las pruebas y el reporte que se pedía. No hay archivo para la etapa 1 (setup y análisis de la consigna).
4. Revisión final: `revision-final.md` se usó para revisar cada rama. `parte-12a-correcciones-codigo.md` y `parte-12b-correcciones-docs.md` son las dos etapas que la siguieron. `reporte-12a.md` es el resumen que el orquestador le pasó a la 12B.
5. Etapa 13, README más corto: `parte-13-readme.md`, posterior a la revisión final.

## Qué modelo ejecutó cada prompt

| Prompt | Quién lo escribió o lo ejecutó | Modelo |
|---|---|---|
| `ESPEC.md` | Orquestador | Claude Opus 5.5 |
| `borrador-dataset.md`, `borrador-holdout.md` | Subagente de IA | No quedó registrado en las notas |
| `parte-02` a `parte-12b` | Orquestador escribió el encargo; subagente implementador lo ejecutó | Claude Opus 5.5 (encargo) y Claude Haiku 5.5 (ejecución) |
| `reporte-12a.md` | Orquestador, como resumen para la 12B | Claude Opus 5.5 |
| `revision-final.md` | Revisores de cada rama, en solo lectura | Claude Opus 5.5 |
| `parte-13-readme.md` | Orquestador escribió el encargo; subagente implementador lo ejecutó | Claude Opus 5.5 (encargo) y Claude Haiku 5.5 (ejecución) |

Las salidas de cada subagente no se copiaron aquí. Están en el historial de cada rama, en los commits y en los reportes de `evals/results/`.
