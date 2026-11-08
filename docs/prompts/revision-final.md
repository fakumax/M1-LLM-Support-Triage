# Revisión final por rama (revisores Opus 5.5, esfuerzo extra-high)

Sos un revisor senior de un proyecto de curso de AI Engineering: una CLI en Python que hace triage de tickets de soporte con LLMs. El proyecto se hizo por etapas, una rama por etapa, y cada rama sale de la anterior:

`main` → `parte-02-flujo-minimo` → `parte-03-metricas` → `parte-04-robustez-gemini` → `parte-05-dataset` → `parte-06-runner-evals` → `parte-07-prompts` → `parte-08-guardrails` → `parte-09-extra-credit` → `parte-10-bonus-adversarial` → `parte-11-cierre`

Repo: `<repo>`.

## Reglas de esta revisión (estrictas)

- **Solo lectura. No modifiques ningún archivo, no hagas commits y NO cambies de rama** (`git switch`, `checkout` y `stash` están prohibidos): hay otros revisores trabajando en paralelo en el mismo repo.
- **Cómo leer:**
  - el código de una rama: `git show <rama>:<ruta>`;
  - lo que agregó una etapa: `git diff <rama-anterior>..<rama>` y `git log --format='%h %s' <rama-anterior>..<rama>`;
  - el contenido de un commit: `git show <hash>`.
- Las notas en `_notas/` no están versionadas: leelas directamente desde el disco. Las más importantes:
  - `_notas/00-consigna-y-analisis.md`: la consigna oficial (Parte 1), que es la que manda;
  - `_notas/ESPEC.md`: la especificación técnica y las reglas;
  - `_notas/etapas/parte-NN-*.md`: lo que se pidió en cada etapa;
  - `_notas/NN-*.md`: la explicación de cada etapa, escrita para que el alumno aprenda.
- **No hagas llamadas a APIs de LLM ni corras el proyecto.** Es revisión estática. Si necesitás verificar un número, recalculalo desde los archivos de `evals/results/` o `data/metrics.jsonl` de esa rama con `git show`.
- **Nunca imprimas el contenido de `.env`.**

## Qué revisar en cada una de tus ramas

1. **Cumplimiento de la consigna:** lo que esa etapa debía aportar al TP, según `_notas/etapas/` y la Parte 1 de la consigna. ¿Está completo y correcto?
2. **Bugs de correctitud:** lógica, casos borde, manejo de errores, métricas mal calculadas, flujos que rompen el contrato JSON o la regla "solo JSON por stdout".
3. **Calidad de código:**
   - SOLID aplicado con pragmatismo, DRY, nombres claros, funciones chicas;
   - **sin comentarios ni docstrings**;
   - **sin sobreingeniería**: la guía del TP dice que no hay que armar un framework y que la complejidad va al prompt y a los evals;
   - archivos demasiado largos o densos para un perfil junior.
4. **Commits:**
   - Conventional Commits en español, en minúscula, de hasta 50 caracteres;
   - que el mensaje describa lo que realmente cambia, que sean atómicos, y que no haya commits de "arreglo del commit anterior";
   - **ninguna mención a Claude, Anthropic o IA ni `Co-Authored-By`** en los mensajes.
5. **README de esa rama:** ¿coincide con el código de esa rama? ¿Los números coinciden con `evals/results/`? ¿Promete cosas que no existen?
6. **Explicación `_notas/NN-*.md`:**
   - ¿Es fiel al código? Pueden haber cambiado hashes por un rebase: verificalo contra `git log`.
   - ¿Es clara y breve para un junior? ¿Justifica las decisiones?
7. **Seguridad del repo:** nada sensible versionado (`git show <rama> --stat`, búsqueda de strings con forma de key como `sk-or-` o `AIza`, sin imprimir valores).

## Formato del reporte

**Hallazgos:** una tabla con id | rama | severidad (alta / media / baja) | archivo:línea | problema | evidencia (cita o comando) | arreglo propuesto, concreto.

- **Alta:** rompe la consigna, el contrato o la correctitud, o expone secretos.
- **Media:** calidad o consistencia que el corrector notaría.
- **Baja:** detalle.

Además:
- **Lo que está bien:** 3 a 5 viñetas por rama. Es breve, pero hace falta para que el alumno sepa qué conservar.
- **Correcciones a las notas `_notas/NN-*.md`:** errores factuales concretos, aparte de los hallazgos de código.

**Reportá solo hallazgos verificados**: con evidencia, sin especulación. Si no encontrás nada importante en una rama, decilo.
