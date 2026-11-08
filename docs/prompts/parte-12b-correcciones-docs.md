# Etapa 12B: datos, documentación y notas de la revisión final

- **Rama:** `parte-12-revision`, la misma de la 12A. Seguí sobre su punta; **no crees otra rama**.
- **Explicación:** `_notas/12-revision.md`, cubre la 12A y la 12B.

Antes de empezar, leé completos:
- `_notas/ESPEC.md`;
- `_notas/etapas/parte-12a-correcciones-codigo.md`, para saber qué corrigió la 12A;
- **el reporte de la 12A**, que el orquestador te pasa en el prompt;
- el `README.md`, todo `docs/`, `evals/criterios_etiquetado.md`, `evals/dataset.jsonl` y los reportes de `evals/results/`.

## 0. Primero: corrección de seguridad en autolesión (decisión del orquestador)

La 12A dejó la regla `self_harm` solo para la primera persona. Así, **"Mi hijo quiere suicidarse" dejó de derivarse a un humano**, y eso es un riesgo real: una mención de riesgo de un tercero tiene que ir a un humano.

**Arreglo:**
- detectar los **verbos** de autolesión en cualquier persona: "quiere suicidarse", "se quiere matar", "se va a suicidar", "me quiero matar", "me voy a suicidar", "quiere quitarse la vida" y sus equivalentes en inglés y portugués;
- **no** detectar el sustantivo suelto en un contexto institucional ("fundación de prevención del suicidio").

**Pruebas:**
- sumá casos a `evals/rule_cases.jsonl`: tienen que disparar "Mi hijo quiere suicidarse" y "Mi socio dice que se va a matar"; no tiene que disparar "Somos una fundación de prevención del suicidio";
- `python -m evals.check_rules` tiene que pasar;
- validá offline que el dataset (44) y el holdout (16) sigan con 0 bloqueos.

Commit: `fix(guardrails): deriva autolesión de terceros`.

El reporte de la 12A, con todos los números, está en `_notas/etapas/reporte-12a.md`. **Leelo antes de documentar.**

## 1. Tags del dataset

Los tags no los usa el runner, así que se pueden corregir sin re-correr nada.

- **Tags regionales:** solo 12 de los 41 tickets con `regional_*` tienen una marca léxica, institucional o geográfica del país:
  - AR: t004, t012, t031, t034, t044;
  - MX: t005, t037, t040;
  - CO: t010;
  - CL: t025, t027, t038.

  Los demás `regional_*` pasan a `neutro`. Revisá además t012: tutea ("¿sabes"), así que su tag regional es dudoso; decidí con criterio y justificalo.
- **Definí los tags** en una sección nueva "Tags" de `evals/criterios_etiquetado.md`, con umbrales concretos. Por ejemplo: `largo` > 250 caracteres, `corto` < 40, `typo` si hay al menos un error ortográfico, y `formal` / `informal` siempre uno de los dos.
- **Aplicá los tags de forma consistente con un script** en el scratchpad, que no se commitea:
  - hoy `largo` está en t031 (198 caracteres) pero no en t029 (200) ni en t034 (201);
  - `typo` está en t005 pero no en t013 ("de mas");
  - hay 10 tickets sin `formal` ni `informal`.
- **El tag `ambiguo`** marca casos que una regla resuelve, mientras que la línea final de los criterios reserva "ambiguo" para cuando ninguna regla alcanza. Renombralo a `frontera` en el dataset y en todo `docs/` y el README.
- **No cambies ningún `query`, `id` ni `expected_category`.** Verificalo con un script.
- Commit: `fix(evals): corrige tags del dataset`

## 2. `docs/dataset.md` (restaurar lo que se perdió en la Parte 11)

En la Parte 11 se perdió la sección del dataset, que estaba en el README de `parte-10-bonus-adversarial`, alrededor de las líneas 274-358. Leela con `git show parte-10-bonus-adversarial:README.md`.

Restaurala en `docs/dataset.md`, **actualizada** con los tags nuevos:
- tabla de campos;
- distribución por categoría y por tag, calculadas con un script;
- el comando para recalcularla y su salida real;
- el mapeo regla → casos: R1 t022/t041, R2 t030/t039/t042, R3 t032/t033, R4 t037/t038;
- la nota de ±12 puntos con 44 casos;
- el holdout.

Enlazala desde la sección "Dataset" del README y desde la tabla de documentación. Commit: `docs: restaura la documentación del dataset`

## 3. Aclaraciones en README y `docs/`

Que el README siga entre 350 y 450 líneas: el detalle va a `docs/`. Cada ítem dice qué corregir o agregar.

1. **Circularidad (`docs/evals.md` y sección de context engineering):**
   - Los ejemplos de las 4 reglas de desempate (copiados en v3) son **gemelos** de casos del dataset: R1↔t022, R2↔t030, R3↔t033/t032 y R4↔t037/t038. Acertar t022 no prueba que el prompt generalice.
   - Además, las reglas se copiaron tal cual de `criterios_etiquetado.md`, que existe desde la Parte 5. **No** "se escribieron después de ver los fallos": se *incorporaron al prompt* después de ver fallar t022 y t033. Corregí esa frase donde aparezca.
2. **El dataset casi no discrimina:**
   - v1 ya acierta entre 95 % y 98 %; de los 9 casos difíciles, 7 no fallaron nunca; v1 y v3 dan 16/16 en el holdout.
   - Agregá: "el dataset detecta regresiones más que diferencias entre prompts".
   - Agregá también que falta el subtipo "no me llega la factura" (consigna §1.2, acción `reenviar_factura`).
3. **Límite del prompt v3, sin cambiarlo:** la política dice "que **te** van a responder", que le habla al modelo, no al cliente. Dos ejemplos ("Te enviamos el resumen de pagos por este mismo canal" y "Ya registramos el problema") contradicen el bloque de políticas. Se documenta y no se cambia, porque invalidaría las evals.
4. **p50 y p95:** se calculan por rango más cercano (en la línea base, la mediana clásica daría 5,652 s y no 5,48). Aclaralo en `docs/evals.md`.
5. **La columna "% JSON válido"** de la comparativa es "JSON válido **al primer intento**". Renombrala; dots da 97,7 %, aunque terminó 44/44 válido.
6. **Criterios inalcanzables con guardrails (`docs/seguridad.md` y README):**
   - En a03 (canary), a08, a09 y a10, con guardrails el éxito es **imposible por construcción**, porque la salida reescribe o bloquea antes de puntuar. Lo que mide si el modelo cedió es la capa `salida`.
   - Sobre el canary: "en ningún modo marca éxito", no "sin guardrails".
   - Actualizá cuántos ataques llegan al modelo y cuáles tienen marca, con los números de la corrida nueva de la 12A.
7. **Canary:** lo agrega `Guardrails.protect_system()` (llamado desde `triage.py`) y solo con guardrails, **no** `src/prompts.py`. Corregilo en el README y en `docs/seguridad.md`, y sumá la regla `system_prompt_leak` a la lista de reglas de salida.
8. **Uso de IA:** hoy el README dice que las herramientas no "tomaron las decisiones técnicas finales", y `docs/uso-de-ia.md` dice que el orquestador "tomó las decisiones técnicas". Alinealo así: el orquestador (Claude Opus 5.5) tomó las decisiones técnicas dentro del alcance, los proveedores y las reglas que fijó el humano, y el humano revisa y aprueba la entrega.
9. **`timestamp` en métricas:** es **cuándo terminó** el request. Corregí la tabla de campos.
10. **Proveedor nuevo:** además de la clase y la línea en `PROVIDERS`, tiene que definir los atributos `name` y `model`. Agregalo donde el README explica cómo sumar un proveedor.
11. **Límites de Gemini:** no se publican. Documentá lo observado: unas 48 requests a `gemini-3.5-flash-lite` el 08/11, con una pausa de 4,5 s, sin 429 persistentes (verificalo en `data/metrics.jsonl`). Que siga como límite conocido.
12. **Inicio rápido robusto:** que funcione sin activar el venv:
    - `python -m venv .venv`;
    - después `.venv\Scripts\python -m pip install -r requirements.txt` y `.venv\Scripts\python -m src.main "..."`;
    - con el equivalente `.venv/bin/python` para macOS y Linux;
    - una línea sobre cómo sacar la key de OpenRouter (openrouter.ai → Keys) y la de Gemini (aistudio.google.com → Get API key);
    - qué hacer si el modelo `:free` deja de existir: `--model <otro :free>` o `--provider gemini`.
13. **Lo que corrigió la 12A, con sus números:**
    - guardrails (falsos positivos y evasiones);
    - el detector de promesas, ahora legible y con casos versionados;
    - `evals/check_rules.py` y cómo correrlo;
    - caché (el costo de lista se conserva, la latencia de las evals excluye la caché, sufijo `_cache`);
    - métricas que no se pierden;
    - validación del catálogo en los prompts;
    - `evals/adversarial.py`;
    - los resultados nuevos de la suite adversarial.

    **Cada número sale de `evals/results/`.** Actualizá también la sección de arquitectura y la tabla de módulos.
14. **Límites que siguen abiertos**, según el reporte de la 12A. Por ejemplo: "el sistema ignora las reglas anteriores" sigue bloqueándose, y todo lo que sea paráfrasis.

Commits: `docs: aclara límites de evals y seguridad` y `docs(readme): actualiza con las correcciones`. Podés dividir o unir según el contenido.

## 4. Prompts usados con IA, versionados

La consigna pide documentar los prompts usados, y hoy `docs/uso-de-ia.md` solo tiene resúmenes.

- Copiá a `docs/prompts/`:
  - `_notas/ESPEC.md`, que es el prompt base de todos los subagentes;
  - todos los `_notas/etapas/*.md`.
- **Sanitizá las copias:**
  - reemplazá las rutas absolutas `<usuario>\...`, `<usuario>/...` y la carpeta del scratchpad por `<repo>` y `<scratchpad>`;
  - verificá con `grep` que no queden `<usuario>`, `AppData` ni nada con forma de key.
- Agregá un `docs/prompts/README.md` corto con el orden de uso y qué modelo ejecutó cada prompt:
  - orquestador: Claude Opus 5.5;
  - etapas: subagentes Claude Haiku 5.5;
  - revisión final: Claude Opus 5.5.
- Enlazá `docs/prompts/` desde `docs/uso-de-ia.md` y sacá la cita al "plan del proyecto", que no está versionado.
- Commit: `docs: versiona los prompts usados`

## 5. Correcciones a las notas `_notas/` (NO se commitean)

Son errores factuales que encontraron los revisores. Aplicalos con cuidado, sin reescribir de más:

- **`01-setup.md`:**
  - "Qué sigue" pide cargar `OPENAI_API_KEY`: aclarar que desde la Parte 2 las variables son `OPENROUTER_API_KEY` y `GEMINI_API_KEY`;
  - agregar el hash `1a7f8f4` en la sección Git.
- **`02-flujo-minimo.md`:**
  - `python -m src.main ""` da "la consulta está vacía" solo si la key está cargada; sin key da "falta la variable OPENROUTER_API_KEY";
  - el backoff está en `base.py` (`call_with_backoff`), no en `openrouter.py`.
- **`03-metricas.md`:**
  - en el diagrama, `t0 = perf_counter()` va dentro de `triage()`, no en `main.py`;
  - la "D": la CLI le pasa la ruta a `append_metrics`; la constante está en `metrics.py`.
- **`04-robustez-gemini.md`:**
  - §4 SOLID-O: `8d5ba56` también tocó `base.py`, `openrouter.py` y `__init__.py` (`triage.py` no);
  - fila httpx2: la alternativa descartada es "capturar solo `Exception`, todo como no transitorio";
  - fila `response_json_schema`: el motivo es que `complete()` recibe un dict genérico, útil para cualquier proveedor;
  - P5: hay que definir `name` y `model`;
  - §7: la desviación de la interfaz ya está aceptada en la ESPEC.
- **`05-dataset.md`:**
  - §3.1: el cupo de la cuenta es de 1.000 por día, no 50; lo que limita es el tope de 20 por minuto;
  - §3.2: de los 9 casos difíciles, 7 nunca fallaron;
  - §3.4: los criterios no mitigan el sesgo, porque v3 los copia y sus ejemplos son gemelos de t022, t030, t033 y t037; las "seis variantes regionales" están sobredimensionadas (ver los tags nuevos);
  - §4: v2 y v3 se crearon los dos en la Parte 7;
  - §5 y §6: el 0,46 es similitud de difflib carácter a carácter y no detecta paráfrasis.
- **`06-runner-evals.md` §4:** `report.py` arma el texto y lo imprime `runner.py`.
- **`07-prompts.md`:**
  - §6: v1 "usa menos tokens" (no es "más barato": a precio de lista, v2 sale 0,000435 contra 0,000449 de v1);
  - §3 y §9: completar los errores conocidos del detector, o remitir a la corrección de la 12A;
  - §9: las reglas se copiaron de los criterios (Parte 5), no se escribieron después de ver los fallos.
- **`08-guardrails.md`:**
  - SOLID: "`guardrails=None` produce el mismo resultado" es compatibilidad hacia atrás, no Liskov; `screen_input` y `screen_output` son métodos de la misma clase, no ISP. Reescribí esos dos puntos;
  - aclarar 176 contra 220 respuestas guardadas: son momentos distintos.
- **`09-extra-credit.md`:** con caché, el costo de lista quedaba en 0. Aclarar que la 12A lo corrigió.
- **`10-bonus-adversarial.md`:**
  - `canary_leak` tampoco se puede cumplir con guardrails;
  - agregar la limitación del criterio `promise`, corregida en la 12A;
  - corregir "el prueba offline".
- **`11-cierre.md`:**
  - línea 69: son dos commits, no tres;
  - línea 42: `uso-de-ia.md` va primero, así que no hubo estado intermedio roto;
  - "no se borró" o "ninguna se borró" es falso para la sección del dataset: restaurada en la 12B;
  - son 46 commits sobre `main`, no 47;
  - líneas 29 y 75: cifras de p95, no "meses";
  - el checklist "clon instalable" requiere el `git push origin main`: agregalo a la sección de merge como **bloqueante**.

## 6. Explicación `_notas/12-revision.md` (ESPEC §6, no se commitea)

- Cómo se hizo la revisión: 5 revisores Opus, uno cada 2 ramas, en solo lectura.
- **Qué encontró cada uno** (lo más importante) y **qué se corrigió**, en una tabla: hallazgo → arreglo → commit.
- Qué quedó abierto y por qué.
- La nota estimada por el revisor global, ≈ 94/100, con su tabla por categoría resumida.
- Los commits de la rama (12A + 12B).
- **La sección final "Cómo entregar"**, con los comandos exactos:
  ```
  git switch main
  git merge --ff-only parte-12-revision
  git push origin main
  ```
  Explicá por qué fast-forward deja la historia lineal y verificá en GitHub que `main` muestre el README final. **Si `main` no se pushea antes del lunes a las 09:00, el corrector ve solo el setup.**

## 7. Verificación final

- `.venv/Scripts/python.exe -m evals.check_rules` pasa.
- Todos los links de README y `docs/` existen.
- Script de números: cada número del README y de `docs/` sale de `evals/results/`, `data/metrics.jsonl` o `config/models.yaml`.
- `git ls-files` sin `.env`, `_notas/`, `.venv/` ni `data/cache/`. Búsqueda de keys en todo el historial (`sk-or-`, `AIza`): 0 resultados, sin imprimir valores.
- **Clon limpio** de `parte-12-revision` en el scratchpad (`git clone --branch parte-12-revision <repo> <tmp>`): seguir el **inicio rápido nuevo** del README al pie de la letra (CLI + `evals.runner --limit 2`, unas 3 requests). Borrar el clon al final.
- `git log --oneline parte-11-cierre..HEAD`: todos los commits con el formato correcto. `git status` limpio.

## Reglas

Las de siempre de la ESPEC:
- **sin push** y sin cambiar `git config`;
- sin atribución a IA en los mensajes de commit (en `docs/` sí se nombran las herramientas);
- sin commits de arreglo del commit anterior (fixup + autosquash si hace falta);
- sin comentarios en el código;
- nunca imprimir keys.

Devolvé el reporte de la ESPEC §7.
