# Decisiones técnicas y limitaciones

Las decisiones con su alternativa descartada y la lista completa de limitaciones. El resumen corto está en el [README](../README.md).

## Decisiones técnicas

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Salida estructurada con el JSON Schema del modelo Pydantic | Pedir "devolvé JSON" en el prompt | El proveedor restringe la forma y el contrato vive en un solo lugar. |
| `max_retries=0` en los SDK y backoff propio | Reintentos internos del SDK | El backoff es visible, respeta `Retry-After` con tope y se configura en el YAML. |
| Errores propios `ProviderError` y `TransientProviderError` | Dejar subir las excepciones del SDK | Liskov: todos los proveedores lanzan lo mismo y la CLI no ve el SDK. |
| El respaldo es un resultado, no una excepción | Lanzar `TriageError` | La CLI no se cae ante un transitorio y cada request genera su línea de métricas. |
| El reintento manda la salida mala y el error como turnos | Reenviar el prompt original | El modelo ve qué falló y corrige. |
| No usar `reasoning.effort=low` | Usarlo para bajar la latencia | La diferencia quedó dentro del ruido y generó más tokens de salida. |
| `gemini-3.5-flash-lite` por defecto | `gemini-3.8-flash` | 2 s contra 182 s en el nivel gratuito (prueba previa, no versionada). |
| Timeout de 120 s | 60 s | Un ticket tardó 39,2 s. |
| v3 como prompt por defecto | v1, más barato | v3 corrige t022 sin fallos nuevos. La ventaja en macro-F1 queda dentro del ruido y así se documenta. |
| Promesas con regex en `src/policy.py` | Juez LLM | Determinista, gratis y auditable. Lo usan la métrica y el guardrail. |
| Guardrails con reglas propias | Endpoint de moderación de OpenAI | No hay key de OpenAI. Las reglas son deterministas y auditables. |
| Riesgo alto bloquea; medio y bajo neutralizan | Bloquear todo lo que coincide | Un `</ticket>` puede venir de un cliente real. |
| Caché MD5 como decorador del proveedor | `if` de caché en `triage()`, o SQLite | `triage()` no cambia y vale para cualquier proveedor. MD5 alcanza porque la caché no protege nada frente a un atacante. |
| Métricas en JSONL, precios en YAML con fuente y fecha | SQLite o constantes en el código | Append-only, versionable y auditable. |
| Dataset sintético y balanceado (11 por categoría) | Tickets reales o clases desbalanceadas | No hay datos de personas. Con clases iguales, una categoría grande no domina el macro-F1. |
| Few-shot separados del dataset | Tomar tickets del dataset como ejemplos | El modelo vería la respuesta antes de la prueba y la métrica quedaría inflada. |
| Autolesión por verbos de intención en cualquier persona | Bloquear el sustantivo "suicidio" | Un tercero que menciona riesgo tiene que llegar a una persona. El sustantivo aparece en contextos institucionales, como una fundación de prevención. |

## Limitaciones

- **Muestra de prompts.** El holdout tiene 16 casos y no separa v1 de v3. Falta validar v3 con más tickets nuevos.
- **Etiquetas.** Falta una segunda revisión independiente del dataset y del holdout.
- **Gemini.** El nivel gratuito no publica límites para `gemini-3.5-flash-lite`. El 08/11 hubo 48 solicitudes de triage (50 llamadas HTTP), ninguna agotó sus reintentos y dos casos reintentaron una vez. Eso no establece el cupo. Para producción, usar el nivel pagado.
- **Holdout de modelos.** El holdout solo se corrió con nemotron. Gemini y dots no se probaron ahí.
- **Tags del holdout.** Sus tags regionales no pasaron por los criterios de la revisión final; los del dataset sí.
- **Guardrails.** Quedan las paráfrasis de injection sin palabra de instrucción, el forzado de `category` y `confidence` sin defensa de código, y las promesas vagas o en pretérito. La detección de odio y de ofensivos usa listas cortas. Falsos positivos aceptados: "me quiero morir de la vergüenza" y "exterminar a las cucarachas".
- **Contrato.** El contrato acepta cualquier string en `actions`. El guardrail de salida descarta las acciones fuera del catálogo, pero el contrato no lo valida.
- **Tokens perdidos.** Si un intento de validación consume tokens y un intento posterior falla con un error no transitorio, esos tokens no se registran.
- **Caché.** Sin expiración, sin límite de tamaño y sin control de escrituras concurrentes.
- **Canary.** Está en el repositorio. Detecta fugas, pero no es un secreto.
- **Reglas de v3.** Para una consulta que no encaja en ninguna regla, v3 pide elegir la categoría más cercana y bajar la confianza, mientras que los criterios piden marcarla como ambigua. El runner no mide esa diferencia.
- **Fechas.** Los reportes usan la hora local sin zona horaria. El registro de métricas usa UTC.
