# Etapa 13: README más corto, detalle en docs/

Rama: `parte-13-readme` (ya creada desde `main`, que tiene todo mergeado). Repo: `<repo>`.

## Por qué

El README tiene 427 líneas. Cumple la consigna, pero está escrito para un auditor: párrafos densos, tablas repetidas y una sección de proceso interno ("Revisión final (12A y 12B)") que al corrector no le aporta. La consigna dice que el README es "la primera impresión": tiene que dejar instalar, configurar, ejecutar y entender las decisiones sin preguntar nada. El detalle va en `docs/`, que ya existe.

## Objetivo

README de **170 a 210 líneas**, con el mismo contenido evaluable, y todo lo que salga del README movido a `docs/`. **No se pierde ningún dato.**

## Lo que la consigna exige en el README (tiene que seguir estando)

1. Setup y uso, con ejemplo de comando y respuesta real.
2. Variables de entorno documentadas (tabla de `.env`).
3. Técnica de context engineering elegida y por qué, con historia de iteración: qué se probó, qué falló, por qué quedó la final.
4. Tabla de resultados de evals.
5. Por qué esos proveedores y el porqué de `temperature` y `max_tokens`.
6. Fórmula del costo y proyección a 400 tickets por día.
7. Guardrails de entrada y salida y **un ejemplo adversarial concreto**.
8. Sección del bonus adversarial (10 ataques, mitigación, efecto medido).
9. Extra credits.
10. Decisiones técnicas clave.
11. Limitaciones.
12. Uso de IA (enlace a `docs/uso-de-ia.md` y `docs/prompts/`).

## Estructura nueva del README

1. `# M1 · LLM Support Triage` y las dos líneas de descripción actuales.
2. **Documentación:** la tabla índice actual, con las dos docs nuevas agregadas.
3. **Inicio rápido:** el bloque de comandos actual. Debajo, en viñetas cortas: Python 3.12 (probado con 3.12.16), clave de OpenRouter obligatoria y de Gemini opcional (ambas gratuitas), no hace falta activar el venv, equivalentes de macOS o Linux. Después, la tabla de variables de `.env`. Absorbe "Requisitos" e "Instalación y configuración".
4. **Uso de la CLI:** la sinopsis, la tabla de opciones, **un** ejemplo real (el de OpenRouter con v3) y el contrato de salida en 3 viñetas (stdout, código 0, código 1).
5. **Arquitectura:** el diagrama de flujo actual y los 5 puntos de SOLID, en una línea cada uno. La tabla de módulos y el árbol de carpetas van a `docs/arquitectura.md`.
6. **Contrato y robustez:** la clase `SupportResponse`, una línea sobre el JSON Schema enviado como salida estructurada, una línea sobre el contrato de respaldo y la tabla de errores. El diagrama de los dos ciclos de reintento y la nota de `max_retries=0` van a `docs/arquitectura.md`.
7. **Proveedores y parámetros:** la tabla de proveedores (la columna de límites, más corta, con la fuente), dos líneas sobre por qué OpenRouter y Gemini, y la tabla de parámetros. "Para sumar un proveedor" va a `docs/arquitectura.md`.
8. **Prompts: técnica e iteración:** la tabla de las tres versiones, la tabla comparativa de resultados y la regla de elección en 3 o 4 líneas (v3 gana por el tercer criterio; la diferencia en macro-F1 queda dentro del ruido). Agregar una línea sobre la circularidad y el holdout (16 de 16 con v1 y con v3). Las notas de chain-of-thought y "Límite del prompt v3" van a `docs/evals.md`, si no están ya.
9. **Evals y dataset:** `python -m evals.runner` y `python -m evals.check_rules` (116 casos sin API), con una línea de qué mide cada uno. Dataset en 3 o 4 viñetas: 44 casos, 11 por categoría, sintético, holdout de 16 y la limitación principal. La tabla de línea base sale del README, porque repite la columna "v1 (1.ª)" de la comparativa y ya está en `docs/evals.md`.
10. **Métricas y costo:** como está; ya es corto.
11. **Seguridad y guardrails:** el diagrama de capas, la tabla de reglas principales, el ejemplo real de injection bloqueada (con stderr y la línea de métricas) y los límites en una línea, con su enlace.
12. **Bonus: resistencia adversarial:** qué ataques son (una línea), el comando, la tabla con y sin guardrails, y 2 o 3 líneas de interpretación: 0 de 20, cota del 16,8 % y que lo que cambia es la capa que frena. El resto ya está en `docs/seguridad.md`.
13. **Extra credits:** la caché en 2 o 3 líneas, la tabla comparativa de modelos y la recomendación en 2 líneas.
14. **Decisiones técnicas:** tabla con las 8 a 10 más importantes. Sí o sí: salida estructurada con JSON Schema; backoff propio; respaldo como resultado; v3 por defecto; guardrails con reglas propias en lugar del endpoint de OpenAI (no hay key); riesgo alto bloquea y medio o bajo neutraliza; caché como decorador; métricas en JSONL y precios en YAML; few-shot separados del dataset. La tabla completa va a `docs/decisiones-y-limitaciones.md`.
15. **Limitaciones:** las 6 o 7 más importantes, en una línea cada una. La lista completa va a `docs/decisiones-y-limitaciones.md`.
16. **Uso de IA:** el párrafo actual, sin cambios.

**Sale entera** la sección "Revisión final (12A y 12B)". Sus datos ya están en `docs/seguridad.md` ("Correcciones de la revisión final") y en `docs/uso-de-ia.md` (etapa 12). Antes de borrarla, verificá cada viñeta: si alguna no está en ningún doc, agregala donde corresponda (`docs/seguridad.md` o `docs/evals.md`). `check_rules` pasa a la sección Evals.

## Docs nuevas

- `docs/arquitectura.md`: tabla de módulos, árbol de carpetas, SOLID con el detalle actual, diagrama de robustez y nota de los reintentos de los SDK, cómo sumar un proveedor, el ejemplo de salida con Gemini y v1, y el comportamiento de las variables de entorno (una variable ya definida gana sobre `.env`; qué hacer si un modelo `:free` cambia de ID).
- `docs/decisiones-y-limitaciones.md`: la tabla completa de decisiones técnicas y la lista completa de limitaciones, tal como están hoy en el README.

## Documentar esta etapa (la consigna pide registrar los prompts de IA)

- `docs/uso-de-ia.md`: agregar `### Etapa 13: README más corto` después de la etapa 12, con el mismo formato (objetivo del prompt, instrucciones clave, decisiones que influyó). La decisión: el README queda como puerta de entrada y el detalle vive en `docs/`, sin perder datos.
- `docs/prompts/parte-13-readme.md`: copia de este archivo con las rutas saneadas (`<repo>`), como las demás.
- `docs/prompts/README.md`: sumar la etapa 13 a "Orden de uso" y a la tabla de modelos. La escribió el orquestador (Claude Opus 5.5) y la ejecutó el subagente (Claude Haiku 5.5).

## Reglas

- **Ningún número nuevo.** Cada número del README nuevo tiene que estar, tal cual, en el README actual o en `docs/`. Copiá las cifras sin redondear ni reformatear.
- **Nada inventado.** Solo se reorganiza y se resume texto existente.
- **Nada perdido.** Cada dato que sale del README tiene que quedar en algún doc. Verificalo antes de terminar.
- **Enlaces relativos válidos.** Sin anclas `#...`, salvo que verifiques que existen. Chequealos con un script en `<scratchpad>`.
- Mismo estilo del README actual: español, impersonal ("Completar", "usar"), frases cortas.
- **No tocar** `src/`, `evals/`, `prompts/`, `config/`, `data/`, `requirements.txt` ni `.env.example`.
- **No commitear y no hacer push.** Los cambios quedan en el working tree de `parte-13-readme`: el usuario los lee antes del commit.
- No modificar `_notas/`, salvo para crear `_notas/13-readme.md`.

## Explicación para el usuario

`_notas/13-readme.md`, corta, con este formato:
- qué se hizo y por qué;
- tabla "sección vieja → dónde quedó";
- checklist de los 12 puntos de la consigna, con la sección del README que cumple cada uno;
- qué responder si en el checkpoint preguntan por qué el README es corto.

## Reporte final (al orquestador)

- Líneas del README nuevo.
- Lista de lo movido, con su destino.
- Viñetas de "Revisión final" que no estaban en ningún doc y dónde quedaron.
- Salida del chequeo de enlaces.
- `git status --short` y `git diff --stat`.
