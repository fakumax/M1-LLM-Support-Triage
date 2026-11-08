# Tarea: borrador del dataset de evaluación (en paralelo a la Parte 2)

**No uses git ni llamadas a APIs. No toques el repo.** Escribí solo en el scratchpad:
`<scratchpad>\dataset\`

Antes de empezar, leé `_notas/00-consigna-y-analisis.md` (la consigna, sobre todo la sección 1.2 con los tickets de ejemplo y la Parte 2 con el análisis del dataset) y la sección "Dataset" de `_notas/ESPEC.md`.

## Contexto

Nubbix es un SaaS ficticio de gestión para pymes de LATAM: facturación electrónica, punto de venta y caja, reportes, inventario, usuarios y permisos, e integraciones como Mercado Pago, bancos y tiendas online. Recibe unos 400 tickets por día. Categorías: `billing`, `technical`, `account`, `other`.

## Entregables (3 archivos)

### 1. `dataset.jsonl`

**44 tickets**, 11 por categoría. Una línea JSON por ticket, UTF-8:

```json
{"id": "t001", "query": "...", "expected_category": "billing", "tags": ["informal", "typo"], "notes": "por qué esta etiqueta, si no es obvio"}
```

- **Que se parezcan a tickets reales:** español de distintos países (AR, MX, CO, CL, PE, UY), con vocabulario local como CFDI, DIAN, SII o AFIP/ARCA cuando aplique.
- **Variedad obligatoria:** formales, informales, con errores de ortografía, todo en mayúsculas, muy cortos ("no anda nada"), largos con contexto, enojados, multi-intención, ambiguos en la frontera entre dos categorías, fuera de dominio (saludos, spam, preguntas sin relación) y 1 o 2 en otro idioma (inglés o portugués) con su categoría real.
- **Al menos 8 casos difíciles** (multi-intención o frontera), con `notes` que expliquen qué regla de desempate se aplicó.
- **No copies** los 8 ejemplos de la consigna; inspirate en ellos.
- **Tags posibles:** `formal`, `informal`, `typo`, `mayusculas`, `corto`, `largo`, `enojado`, `multi_intencion`, `ambiguo`, `fuera_de_dominio`, `otro_idioma`, `regional_xx` (xx = código de país).

### 2. `criterios_etiquetado.md`

Criterios para etiquetar, en español, de unas 40 líneas como máximo:

- **billing:** dinero. Cobros, cargos duplicados, facturas de Nubbix al cliente, reintegros, medios de pago, precio del plan contratado.
- **technical:** algo del sistema no funciona. Errores, caídas, bugs, lentitud, integraciones, sincronización, facturación electrónica que no se emite por un error.
- **account:** acceso e identidad. Login, contraseña, 2FA, usuarios y permisos, datos o email del titular, alta o baja de la cuenta.
- **other:** preventa y comercial (planes nuevos, descuentos, cotizaciones), feedback, saludos, fuera de dominio, spam.
- **Reglas de desempate**, con un ejemplo cada una:
  1. Multi-intención: gana lo que bloquea al cliente o la causa raíz.
  2. Error del sistema al loguearse → `technical`; problema de credenciales o permisos → `account`.
  3. Preguntar por un plan que no tiene → `other`; cobro del plan que ya tiene → `billing`.
  4. Facturación electrónica que el cliente le emite a SUS clientes y falla → `technical`. Factura que Nubbix le emite al cliente → `billing`.

### 3. `fewshot_candidatos.jsonl`

8 ejemplos para el prompt few-shot (2 por categoría). Tienen que ser **distintos de los 44 del dataset**, sin paráfrasis cercanas. Uno de cada par debería ser un caso de frontera. Formato:

```json
{"ticket": "...", "output": {"answer": "...", "confidence": 0.9, "category": "billing", "actions": ["verificar_cobro_duplicado"]}}
```

- `answer`: respuesta al cliente, en español, amable, de 1 a 3 oraciones. No promete reintegros ni descuentos, ni inventa políticas.
- `actions`: solo del catálogo de la ESPEC.

## Control antes de terminar

Corré un script corto con `python` (sin llamadas a APIs) que verifique:
- que los 44 tickets parsean como JSON;
- que los ids son únicos;
- que hay 11 por categoría;
- que no hay tickets repetidos;
- que ningún ticket few-shot está en el dataset.

En tu reporte final incluí ese resultado, la lista de los casos difíciles con su regla, y los archivos generados.
