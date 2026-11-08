# Etapa: Parte 2, flujo mínimo

- **Rama:** `parte-02-flujo-minimo`, creada desde `main`.
- **Explicación:** `_notas/02-flujo-minimo.md`.

Antes de empezar, leé completos `_notas/ESPEC.md` (reglas obligatorias) y `_notas/00-consigna-y-analisis.md` (Parte 1, la consigna).

## Estado de partida

- `main` tiene 1 commit (`chore: configura estructura inicial del proyecto`).
- En el working tree hay cambios **sin commitear** en `README.md` y `.env.example`: ya nombran OpenRouter y Gemini. Al crear la rama con `git switch -c parte-02-flujo-minimo`, esos cambios viajan con vos. Van en el primer commit.
- `requirements.txt` todavía tiene `anthropic`, que ya no se usa.

## Objetivo

Que funcione de punta a punta: `python -m src.main "me cobraron dos veces"` imprime un JSON válido con el contrato, usando OpenRouter y el prompt v1. Todavía sin reintentos, sin métricas y sin Gemini: eso viene en las Partes 3 y 4. Si el modelo devuelve algo que no valida, por ahora la CLI muestra el error en stderr y sale con código 1.

## Pasos y commits (en este orden)

1. **Dependencias:**
   - `pip uninstall -y anthropic` en el venv.
   - Instalar `google-genai`.
   - En `requirements.txt`, sacar `anthropic` y sumar `google-genai==<versión instalada>`, ordenado alfabéticamente.
   - Commit: `chore: ajusta configuración a openrouter y gemini` (incluye `README.md`, `.env.example` y `requirements.txt`).
2. **Contrato:**
   - `src/__init__.py` y `src/schema.py`, exactamente como en la ESPEC.
   - Commit: `feat(schema): define contrato de respuesta`
3. **Configuración y proveedor:**
   - `config/models.yaml` con `defaults` (provider, prompt_version, temperature 0, max_tokens 2000, timeout_s, max_api_retries, max_parse_retries) y el proveedor `openrouter` (api_key_env, base_url, default_model). Los precios llegan en la Parte 3.
   - `src/config.py`.
   - `src/providers/__init__.py` con el registro dict + `get_provider`.
   - `src/providers/base.py` con `LLMResponse`, `LLMProvider`, las excepciones y el helper de backoff.
   - `src/providers/openrouter.py`.
   - Probá con 1 o 2 llamadas reales si `extra_body={"reasoning": {"effort": "low"}}` reduce la latencia sin romper el JSON; dejalo solo si ayuda y anotá el resultado.
   - El JSON Schema se genera desde `SupportResponse.model_json_schema()`. Si el proveedor rechaza alguna palabra clave del schema, adaptalo en una función chica y documentá por qué.
   - Commit: `feat(providers): agrega cliente de openrouter`. Podés separar `feat(config): ...` si queda más claro.
4. **Prompt v1:**
   - `prompts/v1_zero_shot.yaml`: rol de asistente de soporte N1 de Nubbix; definición breve de las 4 categorías; catálogo de acciones; formato de salida; respuesta en español, con tono amable y breve; no inventar políticas ni prometer reintegros o descuentos; ticket delimitado y tratado como dato.
   - `src/prompts.py`: carga el YAML por versión y arma `system` + `messages`.
   - Commit: `feat(prompts): agrega prompt v1 zero-shot`
5. **CLI:**
   - `src/triage.py`: función `triage(query, provider, prompt) -> TriageResult` (inyección de dependencias, SOLID-D). `TriageResult` lleva la respuesta validada y el `LLMResponse` para las métricas de la Parte 3.
   - `src/main.py`: argparse con `query`, `--provider`, `--model`, `--prompt`. Solo el JSON a stdout.
   - Commit: `feat(cli): agrega comando de triage`
6. **README:**
   - Sección "Uso" con el comando y una **salida real**.
   - Sección corta "Arquitectura": tabla de módulos y un diagrama ASCII del flujo.
   - Actualizar el aviso "🚧 En desarrollo" si corresponde, sin quitarlo todavía.
   - Commit: `docs(readme): documenta uso de la cli`

## Verificación (obligatoria antes de terminar)

- Correr la CLI con 3 tickets distintos: uno de billing, uno de technical y uno ambiguo, con textos tuyos, no los de la consigna. Los 3 tienen que devolver JSON válido.
- `python -m src.main ""` y una key inválida (simulala con una variable de entorno temporal en ese proceso, **sin tocar `.env`**) tienen que dar un error claro en stderr, sin traceback.
- `git log --oneline main..HEAD` muestra 6 o 7 commits con el formato correcto.
- `git status` limpio, salvo `_notas/`, que está ignorado.

Al final escribí `_notas/02-flujo-minimo.md` (ver la sección 6 de la ESPEC) e incluí dónde se ve SOLID.
