# Dataset de evaluación

`evals/dataset.jsonl` tiene 44 tickets sintéticos y etiquetados, uno por línea. `evals/holdout.jsonl` tiene 16 tickets nuevos que no se usaron para escribir los prompts. Los criterios de etiquetado (categorías, reglas de desempate y definición de cada tag) están en [criterios_etiquetado.md](../evals/criterios_etiquetado.md). Lo que el dataset mide y lo que no, en la última sección de este documento.

## Campos

| Campo | Contenido |
|---|---|
| `id` | Identificador único: `t001` a `t044` en el dataset, `h001` a `h016` en el holdout. |
| `query` | El ticket en texto libre, como lo escribiría un cliente. |
| `expected_category` | La categoría correcta: `billing`, `technical`, `account` u `other`. |
| `tags` | Atributos del ticket: longitud, registro, ortografía, tono, dominio, idioma, dificultad y región. Un ticket puede tener varios. Las definiciones y los umbrales están en la sección Tags de los criterios. |
| `notes` | Por qué tiene esa categoría. Si aplica una regla de desempate, lo dice (`Regla 1` a `Regla 4`). |

Una línea real del dataset, con sus tags después de la revisión:

```json
{"id": "t002", "query": "se me colgó todo, no responde nada", "expected_category": "technical", "tags": ["corto", "informal", "neutro"], "notes": "Muy corto. Sistema congelado: technical."}
```

## Distribución por categoría

| Categoría | Casos |
|---|---|
| `billing` | 11 |
| `technical` | 11 |
| `account` | 11 |
| `other` | 11 |
| **Total** | **44** |

## Distribución por tag

Un ticket puede tener varios tags, por eso la suma supera 44. Cada ticket tiene exactamente un tag de registro (`formal` o `informal`) y exactamente un tag de región (`regional_ar`, `regional_mx`, `regional_co`, `regional_cl` o `neutro`).

| Tag | Casos |
|---|---|
| `informal` | 32 |
| `neutro` | 32 |
| `formal` | 12 |
| `frontera` | 7 |
| `regional_ar` | 5 |
| `typo` | 5 |
| `corto` | 4 |
| `fuera_de_dominio` | 4 |
| `mayusculas` | 4 |
| `enojado` | 3 |
| `largo` | 3 |
| `regional_cl` | 3 |
| `regional_mx` | 3 |
| `multi_intencion` | 2 |
| `otro_idioma` | 2 |
| `regional_co` | 1 |

Para recalcular las distribuciones por categoría y por tag, desde la raíz del repo en PowerShell:

```powershell
.venv\Scripts\python.exe -c "import json, collections; d = [json.loads(l) for l in open('evals/dataset.jsonl', encoding='utf-8')]; print(len(d), collections.Counter(x['expected_category'] for x in d)); print(collections.Counter(t for x in d for t in x['tags']).most_common())"
```

Salida real:

```text
44 Counter({'billing': 11, 'technical': 11, 'account': 11, 'other': 11})
[('neutro', 32), ('informal', 32), ('formal', 12), ('frontera', 7), ('regional_ar', 5), ('typo', 5), ('corto', 4), ('fuera_de_dominio', 4), ('mayusculas', 4), ('regional_mx', 3), ('enojado', 3), ('largo', 3), ('regional_cl', 3), ('otro_idioma', 2), ('multi_intencion', 2), ('regional_co', 1)]
```

Para el holdout, el mismo comando con `evals/holdout.jsonl` da 16 casos (4 por categoría) y estos tags: `informal` 13, `frontera` 4, `formal` 3, `fuera_de_dominio` 2, `regional_bo` 2, `regional_do` 2, `regional_ec` 2, `regional_gt` 2, `regional_pa` 2, `regional_py` 2, `corto` 1, `multi_intencion` 1, `otro_idioma` 1, `regional_cr` 1, `regional_hn` 1 y `regional_sv` 1.

## Reglas de desempate y casos difíciles

Un caso es difícil si su `notes` cita una regla de desempate: `multi_intencion` para la regla 1 y `frontera` para las reglas 2, 3 y 4. En el dataset hay nueve casos difíciles, y cada regla tiene casos:

| Regla | Casos |
|---|---|
| 1, multi-intención | t022, t041 |
| 2, login y permisos | t030, t039, t042 |
| 3, plan | t032, t033 |
| 4, facturación electrónica | t037, t038 |

Las reglas generales de los criterios no marcan dificultad.

## Cómo se construyó

- Los tickets son sintéticos. Se redactaron para parecerse a tickets reales a partir de los ejemplos de tono de la consigna. No hay tickets reales de Nubbix.
- Está balanceado: 11 casos por categoría. Con clases desbalanceadas, una accuracy alta puede esconder que una categoría chica casi siempre falla.
- Cubre registros formales e informales, enojos (3 casos), errores de tipeo (5), mayúsculas (4), mensajes muy cortos (4) y muy largos (3), consultas fuera de dominio (4) y dos tickets en otro idioma (inglés y portugués).
- Las marcas regionales son de cuatro países: Argentina (5 casos), México (3), Chile (3) y Colombia (1). Son 12 casos con marca. Los otros 32 llevan `neutro`: no tienen una marca que identifique a un país, así que no se les asigna ninguna.
- Los tags se revisaron en la etapa 12B con las definiciones de la sección Tags de `criterios_etiquetado.md`. Cambiaron los tags de 38 de los 44 casos del dataset. `id`, `query`, `expected_category` y `notes` no cambiaron: se verificó con un script de control que no se versiona.
- Los ejemplos few-shot de los prompts v2 y v3 no están en el dataset y no se van a agregar. Si un ejemplo fuera un caso del dataset, el modelo vería la respuesta antes de la prueba y la métrica de ese caso quedaría inflada.

## Holdout

`evals/holdout.jsonl` tiene 16 tickets (`h001` a `h016`, 4 por categoría). Los redactó un subagente de IA sin leer `prompts/`, con los criterios de etiquetado, y el orquestador los revisó. Ninguno repite el dataset: la similitud máxima con sus 44 casos es 0,436 (`difflib.SequenceMatcher`). Cinco casos tienen una regla de desempate en `notes` (h001, h004, h010, h011 y h014), y dos se resuelven con una regla general (h008 y h015).

En la etapa 12B se aplicaron al holdout las mismas definiciones de `frontera`, `multi_intencion` y registro. Los tags regionales de los nueve países del holdout (Paraguay, Bolivia, Guatemala, Ecuador, República Dominicana, Panamá, Costa Rica, El Salvador y Honduras) no pasaron por esos criterios.

## Qué no mide

- **Acciones.** Los casos no tienen acciones esperadas. El runner mide qué porcentaje de las acciones pertenece al catálogo, no si coinciden con una lista exacta, para no castigar una redacción distinta de la misma acción.
- **Intervalo de confianza.** Con 44 casos, la accuracy tiene un intervalo amplio. Con el intervalo exacto de Clopper-Pearson al 95 %: 44 de 44 (100 %) va de 92,0 % a 100 %, y 42 de 44 (95,5 %, primera corrida de v1) va de 84,5 % a 99,4 %. La cifra de ±12 puntos que aparecía antes vale para una accuracy de 80 % (±11,8 con la aproximación normal). Con accuracies altas el intervalo es asimétrico, y un caso equivale a 2,3 puntos. Diferencias de un caso no son concluyentes.
- **Discriminación entre prompts.** El dataset detecta regresiones más que diferencias entre prompts. v1 ya acierta entre 95,5 % y 97,7 % (42 y 43 de 44 en sus dos corridas), y de los nueve casos difíciles, siete nunca fallaron. Solo t022 y t033 fallaron, y solo en v1 y v2. v1 y v3 dan 16 de 16 en el holdout.
- **Subtipo ausente.** Falta el subtipo "no me llega la factura" de la consigna (§1.2, acción `reenviar_factura`). Ningún caso lo tiene, así que el dataset no mide esa acción.
- **Circularidad.** Las reglas de v3 salen de los mismos criterios con que se etiquetó el dataset. Ver [evals.md](evals.md).
