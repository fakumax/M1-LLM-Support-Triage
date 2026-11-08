# ESPEC: especificación técnica común (leer completa antes de trabajar)

Esta es la fuente de verdad técnica del proyecto. La consigna oficial está en `_notas/00-consigna-y-analisis.md` (Parte 1). Si algo de acá contradice la consigna, gana la consigna; avisá en tu reporte.

## 1. Entorno

- Carpeta del repo: `<repo>` (en Git Bash: `<repo>`).
- Python: siempre con `.venv/Scripts/python.exe` (3.12.16). Instalar con `.venv/Scripts/python.exe -m pip install ...`.
- **Todo se ejecuta desde la raíz del repo**:
  - CLI: `python -m src.main "<consulta>"`
  - Runner: `python -m evals.runner`
- Las keys están en `.env`: `OPENROUTER_API_KEY` y `GEMINI_API_KEY`. **Nunca** imprimas, loguees ni commitees sus valores ni el contenido de `.env`.
- Versiones instaladas, más nuevas que tu entrenamiento. Verificá la API inspeccionando el paquete instalado, no de memoria.
  - `openai` 3.46.0: `client.chat.completions.create(...)` funciona; `resp.usage.model_extra.get("cost")` trae el costo que reporta OpenRouter.
  - `pydantic` 2.14.3.

## 2. Reglas de git (obligatorias)

- **Ramas:**
  - Cada etapa trabaja en su rama, creada desde la punta de la rama de la etapa anterior: `git switch <rama-anterior>` y después `git switch -c <rama-nueva>`.
  - Nunca commitear en `main`.
- **Lo que nunca se hace:** `git push`, cambiar `git config`, reescribir commits de otras ramas, `--no-verify`.
- **Mensajes de commit:**
  - Conventional Commits: `tipo(alcance): descripción`.
  - En **español**, en minúscula, **50 caracteres como máximo**, sin punto final, verbo en tercera persona ("agrega", "define", "registra").
  - Sin cuerpo salvo que haga falta.
  - **Prohibido** `Co-Authored-By` o cualquier mención a Claude, Anthropic o IA en el commit.
- **Antes de cada commit:** `git status --short` y `git diff --staged --stat`. Nunca se stagean `.env`, `.venv/`, `_notas/`, `__pycache__/` ni `data/cache/`. Usá `git add <archivos>` explícitos, nunca `git add -A`.
- Cada commit es una unidad lógica y deja el proyecto funcionando.
- **Nada de commits de "arreglo del commit anterior"** (`style:` por largo de línea, typos, etc.). Revisá el formato **antes** de commitear: líneas de 120 caracteres como máximo, `py_compile` y sin comentarios. Si igual se te escapa algo en un commit de tu propia rama que todavía no tiene ramas encima, fusionalo con `git commit --fixup <hash>` y `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <rama-anterior>`. Después verificá con `git diff <tip-original> HEAD` que el árbol quedó igual.

## 3. Reglas de código

- Identificadores y código en inglés. Textos para el usuario final (answers, README, docs) en español.
- **Sin comentarios ni docstrings**, salvo un "por qué" muy corto donde no sea obvio.
- Funciones chicas, type hints, una responsabilidad por archivo. **No armes un framework**: la complejidad va al prompt y a los evals.
- El runner es un script simple (sin pytest ni frameworks de testing).
- **SOLID, aplicado con pragmatismo**: lo pide el usuario. Cada principio se cumple de forma concreta y visible, sin capas de más:
  - **S (responsabilidad única):** un módulo por responsabilidad: cliente LLM, validación, prompts, guardrails, métricas, CLI. `main.py` solo parsea argumentos e imprime; la lógica vive en `triage.py`.
  - **O (abierto/cerrado):** agregar un proveedor es crear una clase nueva y registrarla en `providers/__init__.py` (un dict nombre → clase). `triage.py` no se toca.
  - **L (sustitución de Liskov):** cualquier `LLMProvider` es intercambiable: devuelve el mismo `LLMResponse` y lanza las mismas excepciones (`ProviderError` / `TransientProviderError`), nunca las del SDK.
  - **I (segregación de interfaces):** interfaces mínimas: `LLMProvider` expone solo `complete(...)`; los guardrails de entrada y de salida son funciones separadas.
  - **D (inversión de dependencias):** `triage()` recibe el `LLMProvider` (y el prompt) ya construidos como parámetros, y depende de la abstracción, no del SDK concreto. La CLI y el runner arman las dependencias y se las pasan.
- En la explicación de cada etapa, si aplica, indicá en una línea dónde se ve SOLID en lo que hiciste.
- Dependencias: solo las de `requirements.txt`. Si agregás una, fijá la versión exacta con `==`.
- La salida de la CLI va **solo** a stdout como JSON (`json.dumps(..., ensure_ascii=False, indent=2)`), con `sys.stdout.reconfigure(encoding="utf-8")`. Mensajes, avisos y errores van a stderr.
- El README se actualiza en cada etapa, en español, y **solo documenta lo que existe y funciona**. Los ejemplos de salida tienen que ser reales (copiados de una ejecución).

## 4. Uso de APIs (cuota y costo)

- **OpenRouter:** solo modelos que terminan en `:free`. La key tiene tope de gasto USD 0. Límites: 20 requests/minuto y 1.000/día. En corridas largas espaciá las llamadas (≥ 3,2 s entre requests).
- **Gemini:** nivel gratuito de AI Studio. Verificá los límites vigentes en la documentación oficial antes de correr evals.
- Minimizá llamadas: probá con 2 o 3 tickets y corré el dataset completo solo cuando la etapa lo pide.
- Los modelos gratis de OpenRouter **razonan antes de responder** (400 a 1.500 tokens de razonamiento), así que `max_tokens` tiene que dejar lugar para eso (default 2000). Ya se vio en la práctica: JSON roto, salidas cortadas por `max_tokens` y un modelo que generó solo espacios en blanco.

## 5. Arquitectura

```
src/
  __init__.py
  main.py              CLI (argparse)
  config.py            carga .env (python-dotenv) y config/models.yaml
  schema.py            SupportResponse (contrato)
  prompts.py           carga prompts/*.yaml y arma los mensajes
  triage.py            orquesta: guardrails → prompt → LLM → validación/reintento → guardrails → métricas
  metrics.py           costo + append a data/metrics.jsonl
  guardrails.py        (Parte 8) entrada y salida
  cache.py             (Parte 9) caché MD5
  providers/
    __init__.py        get_provider(name, model) -> LLMProvider
    base.py            LLMResponse, LLMProvider (ABC), ProviderError, TransientProviderError, backoff
    openrouter.py      OpenRouterProvider (SDK openai con base_url de OpenRouter)
    gemini.py          (Parte 4) GeminiProvider (SDK google-genai)
prompts/               v1_zero_shot.yaml, v2_few_shot.yaml, v3_*.yaml
config/models.yaml     defaults, proveedores, modelos y precios (con fuente y fecha)
evals/
  __init__.py
  dataset.jsonl        ≥ 30 casos (Parte 5)
  criterios_etiquetado.md
  runner.py            (Parte 6)
  adversarial.jsonl    (bonus)
  results/             reportes .json y .md de cada corrida (se versionan)
data/metrics.jsonl     se versiona (el checklist pide al menos una ejecución registrada)
```

### Contrato (no cambia nunca)

```python
Category = Literal["billing", "technical", "account", "other"]

class SupportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    category: Category
    actions: list[str] = Field(min_length=1)
```

`actions` son strings `snake_case` en español, preferentemente de este catálogo, que el prompt le pasa al modelo:

- `verificar_cobro_duplicado`, `gestionar_reintegro`, `reenviar_factura`, `actualizar_medio_de_pago`, `explicar_cargos`
- `revisar_logs_del_error`, `verificar_estado_de_integracion`, `solicitar_capturas_o_pasos`, `escalar_a_soporte_tecnico_n2`
- `restablecer_acceso`, `gestionar_usuarios_y_permisos`, `actualizar_datos_de_la_cuenta`, `verificar_identidad_del_titular`
- `derivar_a_ventas`, `solicitar_mas_informacion`, `derivar_a_agente_humano`

### Estado real del código (aceptado por el orquestador, actualizado al cerrar la Parte 4)

- `LLMResponse` suma `attempts: int = 1`: los reintentos de transporte que hizo el proveedor.
- `LLMProvider` expone los atributos `name` y `model`, además de `complete()`. `triage()` los necesita para las métricas cuando cae en el respaldo.
- `triage(query, provider, prompt, max_parse_retries) -> TriageResult`. `TriageResult` es plano: `response`, `provider`, `model`, `prompt_tokens`, `completion_tokens`, `reported_cost_usd`, `latency_s`, `attempts`, `fallback`, `guardrail`.
- El parseo tolerante vive en `src/parsing.py`.
- (Parte 6) `src/pipeline.py`: `build_triage_deps(...)` arma `TriageDeps` y `triage_and_register(query, deps, source)` corre `triage` y registra la métrica; lo comparten la CLI y el runner.
- (Parte 6) `evals/runner.py` (CLI del runner), `evals/scoring.py` (métricas puras) y `evals/report.py` (reportes `.json` y `.md`).
- (Parte 7) `src/policy.py`: `find_promises(answer)`. Lo usan el scoring y el guardrail de salida. El prompt por defecto es **v3** (`prompts/v3_few_shot_reglas.yaml`).
- (Parte 8) `src/guardrails.py`, inyectado en `triage()` como dependencia opcional.
  - `TriageResult.guardrail` es una **lista de códigos** o `None`.
  - Un bloqueo devuelve el contrato seguro con `fallback=true` y `attempts=0` si no se llamó al modelo.
  - `FALLBACK_ANSWER` y `fallback_response()` viven en `src/schema.py`.
  - El canary está en `config/models.yaml`.
  - Flag `--no-guardrails` en la CLI y en el runner. El reporte del runner cuenta las activaciones.
- (Parte 9) `src/cache.py`: `CachedProvider`, decorador de `LLMProvider` con clave MD5 y archivos en `data/cache/` (ignorada por git).
  - Flag `--cache` en la CLI y en el runner.
  - `LLMResponse` y `TriageResult` tienen `cached`.
  - El runner tiene `--dataset` y existe `evals/holdout.jsonl` (16 casos fuera de muestra).
  - La pausa del runner solo se espera después de una llamada real.
- (Parte 6) `src/schema.py` expone `ACTION_CATALOG` y `CATEGORIES`. `TriageResult` suma `invalid_responses`. `config/models.yaml` tiene `eval_sleep_s` por proveedor.
- `httpx2` está fijado en `requirements.txt` porque `gemini.py` lo importa directamente.
- `config/models.yaml` tiene `timeout_s: 120` y `max_retry_after_s: 30`, y los precios en `providers.<p>.models.<id>`.

### Proveedores

- `LLMResponse` (dataclass): `text`, `prompt_tokens`, `completion_tokens`, `latency_s`, `provider`, `model`, `reported_cost_usd: float | None`.
- `LLMProvider.complete(system: str, messages: list[dict], json_schema: dict) -> LLMResponse`. Cada `messages[i]` es `{"role": "user"|"assistant", "content": str}`; así un reintento puede mandar la salida mala y el error.
- **OpenRouter:**
  - `base_url="https://openrouter.ai/api/v1"`.
  - `response_format={"type": "json_schema", "json_schema": {"name": "support_response", "strict": True, "schema": ...}}`.
  - Probar `extra_body={"reasoning": {"effort": "low"}}` y dejarlo si baja la latencia sin romper la salida.
  - Modelo por defecto: `nvidia/nemotron-3.5-super-vl:free`, el más rápido y estable en la prueba del 08/11.
  - Mandar el header `X-Title: llm-support-triage`.
- **Errores:**
  - `TransientProviderError` (429, 5xx, timeout, conexión): se reintenta con backoff exponencial (1 s, 2 s, 4 s; máximo `max_api_retries`), respetando `Retry-After` si viene. Los reintentos internos de los SDK se desactivan (`max_retries=0`) para que el manejo sea explícito.
  - `ProviderError` (401, 400, falta la key): no se reintenta; la CLI muestra un mensaje claro en stderr y sale con código 1.

### Triage, reintento y respaldo (Parte 4)

- Extraer el JSON de forma tolerante: sacar los cercos de código y tomar el primer objeto `{...}`. Validar con `SupportResponse.model_validate`.
- Si falla, reintentar hasta `max_parse_retries` (2): agregar la salida del modelo como `assistant` y un `user` con el error de validación resumido.
- Si se agotan los reintentos o los errores transitorios, devolver el **contrato de respaldo**: `answer` = "No pudimos procesar tu consulta automáticamente. Un agente de soporte la va a revisar.", `confidence=0.0`, `category="other"`, `actions=["derivar_a_agente_humano"]`. Marcar `fallback=true` en las métricas. **La CLI nunca se cae por un error transitorio.**
- Tokens y latencia de todos los intentos se suman.

### Métricas (`data/metrics.jsonl`, una línea por request de triage)

```json
{"timestamp": "2026-11-08T17:00:00+00:00", "source": "cli|eval|adversarial", "provider": "openrouter", "model": "...", "prompt_version": "v1",
 "prompt_tokens": 120, "completion_tokens": 450, "total_tokens": 570, "latency_s": 7.12,
 "cost_usd": 0.0, "cost_usd_list_price": 0.00034, "attempts": 1, "fallback": false,
 "category": "billing", "guardrail": null}
```

- `cost_usd` = tokens × precio real del modelo usado (0 en los `:free`), desde `config/models.yaml`.
- `cost_usd_list_price` = tokens × precio de lista de un modelo pago de referencia (la variante paga del mismo modelo si existe), **con la URL de origen y la fecha** en `config/models.yaml`. Así el costo es reproducible y auditable con la fórmula `tokens_in × precio_in / 1e6 + tokens_out × precio_out / 1e6`.

### Prompts (`prompts/*.yaml`)

```yaml
version: v1
technique: zero-shot
description: ...
system: |
  ...
user_template: |
  <ticket>
  {ticket}
  </ticket>
examples: []
```

En v2 en adelante, `examples` es una lista de `{ticket, output}`. Los ejemplos **no pueden estar en `evals/dataset.jsonl`**. El ticket siempre va delimitado y el system prompt aclara que es un dato, nunca una instrucción.

### Dataset (`evals/dataset.jsonl`)

```json
{"id": "t001", "query": "...", "expected_category": "billing", "tags": ["informal", "typo"], "notes": "..."}
```

### CLI

```
python -m src.main "<consulta>" [--provider openrouter|gemini] [--model ID] [--prompt v1] [--no-guardrails]
```

`--no-guardrails` se agrega en la Parte 8. Los valores por defecto salen de `config/models.yaml`.

## 6. Explicación de cada etapa (obligatoria, NO se commitea)

Al terminar, escribí `_notas/NN-nombre.md` en español, para un AI Engineer junior que está aprendiendo. Máximo unas 150 líneas, claro y sin relleno:

1. Rama y commits (hash + mensaje).
2. Qué se hizo (lista corta).
3. **Decisiones y por qué** (tabla: decisión | alternativa descartada | por qué).
4. Diagrama ASCII si ayuda a entender el flujo.
5. Cómo probarlo (comandos de PowerShell desde la raíz, con la salida esperada).
6. Qué responder si te lo preguntan en el checkpoint (3 a 5 preguntas con respuesta breve).
7. Limitaciones o pendientes.

## 7. Reporte final al orquestador

Devolvé:
- un resumen;
- la rama y los commits (`git log --oneline <rama-anterior>..HEAD`);
- los comandos que corriste y sus resultados (las llamadas reales a la API y su salida);
- los problemas encontrados y las decisiones que tomaste o que el orquestador tiene que tomar.
