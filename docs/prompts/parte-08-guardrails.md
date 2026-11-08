# Etapa: Parte 8, guardrails de entrada y salida

- **Rama:** `parte-08-guardrails`, creada desde la punta de `parte-07-prompts`.
- **Explicación:** `_notas/08-guardrails.md`.

Antes de empezar, leé completos `_notas/ESPEC.md`, las explicaciones `_notas/02` a `_notas/07`, el código de `src/` y la Parte 1 de `_notas/00-consigna-y-analisis.md` (seguridad).

## Objetivo

La consigna pide *"mitigar prompt injection y aplicar moderación de entrada y salida"*, con al menos un guardrail de entrada y uno de salida. La guía agrega: *"pensá en capas"* y *"documentá con un ejemplo concreto qué detectaste, qué decisión tomó el sistema y por qué"*. **No hay endpoint de moderación de OpenAI**, porque no hay key de OpenAI: la moderación se resuelve con reglas propias, documentadas.

## Diseño (`src/guardrails.py`, funciones chicas, SOLID-I)

### Entrada, antes de llamar al LLM

1. **Validación:** consulta vacía (ya existe) y consulta demasiado larga. Recortar a un máximo configurable (por ejemplo 4.000 caracteres) y marcarlo.
2. **Detección de injection o jailbreak por patrones:**
   - En español, inglés y portugués: "ignorá / ignore / ignore as instruções…", "olvidá tus instrucciones", "system prompt", "revelá / repetí tus instrucciones", "actuá como / act as / you are now", "DAN", "modo desarrollador", "jailbreak".
   - Marcadores de rol (`<|system|>`, `### system`, `[INST]`) e intento de cerrar el delimitador (`</ticket>`).
   - Bloques largos en base64.
   - Resultado: un nivel de riesgo.
3. **Decisión:**
   - Riesgo alto: **bloquear sin llamar al LLM**. Se devuelve un contrato seguro: `category: "other"`, `confidence: 0`, `actions: ["derivar_a_agente_humano"]` y un `answer` genérico y amable.
   - Riesgo bajo o medio: seguir, pero **neutralizar** el texto (escapar o eliminar los delimitadores `<ticket>`/`</ticket>` y los marcadores de rol).
   - Se registra `guardrail` con el código de la regla.
4. **Moderación de entrada:**
   - Amenazas de violencia, odio o autolesión: bloquear y derivar a un humano.
   - **Un cliente enojado o con insultos NO se bloquea**: en soporte es normal, y hay tickets así en el dataset (t009, t022).
5. **Datos sensibles:** si el ticket tiene un número de tarjeta (validado con Luhn), **enmascararlo** antes de mandarlo al LLM. Es privacidad y es una capa más.

### Salida, después de validar el contrato

1. **Fuga del system prompt:**
   - Un **canary token**, un string aleatorio fijo en la configuración, se inserta en el system prompt al armarlo; no hace falta tocar los YAML de prompts.
   - Si aparece en la salida, o aparece un fragmento literal largo del system prompt, se bloquea y se devuelve el contrato seguro.
2. **Promesas indebidas:**
   - **Reusá `find_promises()` de `src/policy.py`**, que creó la Parte 7 para medir promesas en las evals. No dupliques patrones: si te falta alguno, agregalo ahí.
   - Se reemplaza `answer` por una respuesta segura que dice que un agente lo revisa. `category` se mantiene. Se agrega `derivar_a_agente_humano` a `actions` si no está, `confidence` queda en `min(conf, 0.5)` y se registra `guardrail`.
3. **Moderación de salida:** términos ofensivos o tóxicos en `answer` → respuesta segura.

### Integración

- `triage()` recibe los guardrails como dependencia opcional (SOLID-D). La CLI y el runner los arman.
- Flag `--no-guardrails` en la CLI y en el runner, para medir el efecto en la Parte 10.
- `TriageResult.guardrail` y la métrica `guardrail` guardan los códigos que se activaron, o `null`.

## Notas del orquestador después de la Parte 7

- **El prompt por defecto ahora es v3.** Usalo en todas las corridas.
- **`src/policy.py`** (`find_promises`) tiene un falso positivo conocido ("te devolvemos la llamada") y falsos negativos vagos ("a la brevedad"). Corregí el falso positivo, porque ahora va a reescribir respuestas reales. Mantené la función simple y legible: si una regla nueva complica mucho el regex, preferí no agregarla y documentá la limitación.

## Pasos y commits

1. Guardrails de entrada, incluido el enmascarado de tarjetas. Commit: `feat(guardrails): agrega guardrails de entrada`
2. Guardrails de salida, con canary y promesas. Commit: `feat(guardrails): valida contenido de la salida`
3. Flag `--no-guardrails` en la CLI y en el runner. Commit: `feat(cli): permite desactivar guardrails`
4. **Falsos positivos:**
   - Corré la suite completa (44 casos) con guardrails y el prompt ganador de la Parte 7.
   - **Ningún ticket legítimo del dataset tiene que quedar bloqueado.** Si alguno queda, ajustá los patrones y documentalo.
   - Reportá también cuántas respuestas cambió el guardrail de promesas.
   - Commit: `chore(evals): corre la suite con guardrails`
5. **README:** sección "Seguridad y guardrails" con:
   - un diagrama de las capas;
   - una tabla de reglas (capa, qué detecta, decisión, por qué);
   - **un ejemplo concreto real**: el comando con un ticket malicioso, la salida y la línea de métricas con `guardrail`, explicando qué se detectó y por qué se decidió eso;
   - las limitaciones: los patrones se evaden con paráfrasis, y por eso hay varias capas.
   - Commit: `docs(readme): documenta guardrails`

## Verificación

- Pruebas offline de cada regla, con un script en el scratchpad que no se commitea: casos que tienen que disparar y casos que **no** (por ejemplo "ignoré el mail de ustedes" no es una injection).
- 2 o 3 pruebas reales de la CLI con ataques.
- `git log --oneline parte-07-prompts..HEAD`: commits con el formato correcto. `git status` limpio.

Al final escribí `_notas/08-guardrails.md` (ESPEC §6): defensa en capas con un diagrama, por qué bloquear vs. neutralizar, y por qué no se bloquea a un cliente enojado. Devolvé el reporte de la ESPEC §7.
