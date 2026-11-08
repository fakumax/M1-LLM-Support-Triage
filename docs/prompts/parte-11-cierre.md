# Etapa: Parte 11, cierre (README final, uso de IA y ejecución limpia)

- **Rama:** `parte-11-cierre`, creada desde la punta de `parte-10-bonus-adversarial`.
- **Explicación:** `_notas/11-cierre.md`.

Antes de empezar, leé completos:
- la consigna entera, incluida la guía y la sección de evaluación (`_notas/00-consigna-y-analisis.md`, Parte 1);
- `_notas/ESPEC.md`;
- **todas** las explicaciones `_notas/01` a `_notas/10`;
- el README actual;
- el código completo.

## Objetivo

Dejar el repo listo para entregar. El checklist oficial pide:
- claves por variables de entorno;
- `src/main.py` versionado;
- al menos una ejecución registrada;
- evals corridas con resultados en el README;
- **README y código consistentes**: quien clone el repo tiene que poder instalarlo y correrlo sin preguntar nada.

## Pasos y commits

1. **README final**, reestructurado para leerse de arriba a abajo:
   1. título y una línea de qué hace;
   2. el contexto (Henry M1, Nubbix ficticio);
   3. inicio rápido de 5 comandos;
   4. requisitos, instalación y configuración;
   5. uso de la CLI con ejemplos reales;
   6. arquitectura (diagrama + módulos + dónde se aplica SOLID);
   7. contrato JSON;
   8. proveedores y parámetros (por qué esos valores);
   9. robustez;
   10. métricas y costo;
   11. dataset;
   12. evals;
   13. context engineering y elección del prompt;
   14. seguridad y guardrails;
   15. bonus adversarial;
   16. extra credits;
   17. decisiones técnicas (tabla de decisión → por qué);
   18. limitaciones;
   19. uso de IA.

   **El README actual tiene 863 líneas: es demasiado largo para leerse.** Objetivo: **350 a 450 líneas**.
   - Cada sección del README queda con lo esencial: qué es, el número clave y por qué.
   - El detalle va a archivos en `docs/`, enlazados desde la sección correspondiente:
     - `docs/evals.md`: todas las tablas de corridas, prompts, holdout y comparativa;
     - `docs/seguridad.md`: reglas de guardrails, ejemplos y la suite adversarial completa;
     - `docs/metricas-y-costos.md`;
     - `docs/uso-de-ia.md`.
   - **No se pierde información:** se mueve.
   - Verificá con un script que cada número del README siga coincidiendo con `evals/results/`.

   Reglas:
   - Sacá "🚧 En desarrollo" y cualquier "Pendiente" que ya esté resuelto.
   - No inventes números: cada número sale de `evals/results/` o de `data/metrics.jsonl`.
   - Cuidá que no sea eterno: lo que no aporte, afuera.
   - Commit: `docs(readme): completa documentación final`
2. **Uso de IA**, en `docs/uso-de-ia.md`, enlazado desde el README. La consigna pide documentar los prompts usados y cómo influyeron en las decisiones. Contenido:
   - **Herramientas:** Claude Code como orquestador, con subagentes por etapa. Los prompts de cada etapa están resumidos ahí; el detalle completo vive en las instrucciones de cada etapa.
   - **Para cada etapa:** el prompt resumido (objetivo e instrucciones clave) y qué decisiones influyó.
   - **Decisiones que salieron de experimentos guiados por IA** (el orquestador las listó; verificalas con las explicaciones):
     - descartar OpenCode Go por sus condiciones de uso;
     - descubrir que los modelos gratis razonan y que hace falta `max_tokens` ≥ 2000;
     - que un modelo de OpenRouter generó solo espacios en blanco, de ahí la validación y los reintentos;
     - Gemini flash-lite prometió un reembolso, de ahí las políticas en el prompt y el guardrail de salida;
     - flash-lite por defecto en Gemini porque el 3.8-flash tardó 182 s;
     - timeout de 120 s porque un request tardó 39 s;
     - la elección del prompt por macro-F1;
     - el resto, según las explicaciones.
   - **Lista completa de decisiones** (orquestador, actualizada al cerrar la Parte 9). Verificá cada una contra las explicaciones `_notas/NN-*.md`:
     1. **Proveedores:** no había API de OpenAI ni de Anthropic, solo suscripciones. Se eligieron OpenRouter (modelos gratis, cupo de 1.000 por día) y Gemini (AI Studio, nivel gratuito). OpenCode Go se descartó porque sus condiciones lo limitan a agentes de código.
     2. **Prueba de modelos gratis:** razonan antes de responder (de 400 a 1.500 tokens), así que `max_tokens` es 2000. Un modelo devolvió solo espacios en blanco y otro JSON cortado: de ahí la validación con Pydantic y los reintentos.
     3. **`reasoning.effort=low`:** se midió y no se adoptó, porque la diferencia quedó dentro del ruido.
     4. **Gemini 3.8-flash** tardó 182 s, así que flash-lite quedó por defecto. **Flash-lite prometió un reembolso:** de ahí las políticas de v3, la métrica de promesas y el guardrail de salida.
     5. **Timeout:** 120 s, porque un request tardó 39 s con un timeout de 60.
     6. **Elección del prompt con efecto techo** (v1 dio 95,5 %): se midió el ruido entre dos corridas del v1 y la regla de elección quedó en este orden: macro-F1 por encima del ruido, promesas, fallos corregidos y costo. Ganó v3.
     7. **Circularidad** (v3 usa los criterios del dataset): se agregó un holdout de 16 tickets escrito por un agente que no vio los prompts. v1 y v3 dieron 100 %: v3 no empeora, pero no se demuestra que sea mejor.
     8. **Guardrails en capas**, con 0 falsos positivos en los 44 tickets legítimos. Un cliente enojado no se bloquea.
     9. **Comparativa:** los 3 modelos dieron 100 %. Gemini flash-lite fue el más rápido, y quedó como recomendación para producción en el nivel pagado. Dots inventó acciones con typos, y de ahí el guardrail de acciones fuera del catálogo (Parte 10).
     10. **Caché MD5** como decorador del proveedor, para re-correr las evals sin gastar cuota.
     11. **Historia de git limpia:** los commits de "arreglo del commit anterior" se fusionaron con fixup y autosquash, verificando que el árbol quedara idéntico.
   - **Herramientas, con los modelos:**
     - Claude Code con **Claude Opus 5.5** como orquestador: diseño, especificación, revisión de cada etapa y decisiones.
     - **Subagentes Claude Haiku 5.5** (esfuerzo extra-high) para implementar cada etapa.
     - Revisión final de cada rama con **Opus 5.5**.
   - **Qué decidió el humano:**
     - el alcance y avanzar por partes en ramas separadas;
     - los proveedores (OpenRouter y Gemini, gratis);
     - Conventional Commits en español, sin atribución a IA y sin push automático;
     - código sin comentarios y SOLID;
     - Python 3.12.16;
     - la revisión final con Opus.
   - Commit: `docs: documenta el uso de ia`
3. **Ejecución limpia (checklist oficial):**
   - `git clone` del repo local a una carpeta temporal **fuera del repo**. Para que el clon tenga la rama actual: `git clone --branch parte-11-cierre <ruta-del-repo> <tmp>`.
   - `python -m venv .venv` con el Python 3.12 de uv: está en `<usuario>\.local\bin\python.exe`.
   - `pip install -r requirements.txt`.
   - Copiar `.env` al clon temporal (solo ahí, nunca dentro del repo versionado).
   - Correr la CLI con un ticket y el runner con `--limit 2`. Los dos tienen que andar siguiendo **solo** el README.
   - Borrar el clon temporal.
   - Si algo del README no funcionó tal como está escrito, corregilo. Commit: `docs(readme): corrige pasos de instalación`
4. **Controles finales:**
   - `git ls-files` no incluye `.env`, `_notas/`, `.venv/`, `__pycache__/` ni `data/cache/`.
   - Buscá en todo el historial versionado strings con forma de key (`sk-or-`, `AIza`): no tiene que haber ninguno. Reportá el comando y el resultado sin imprimir valores.
   - Todos los links internos del README apuntan a archivos que existen.
   - `requirements.txt` coincide con lo que se importa.

## Verificación

- `git log --oneline parte-10-bonus-adversarial..HEAD`: commits con el formato correcto. `git status` limpio.

Al final escribí `_notas/11-cierre.md` (ESPEC §6) con:
- el checklist de entrega marcado con evidencia;
- cómo se hace el merge final a `main` (`git switch main` y `git merge --ff-only <última rama>`) y por qué fast-forward deja la historia lineal;
- la guía de 10 minutos para defender el proyecto en el checkpoint.

Devolvé el reporte de la ESPEC §7.
