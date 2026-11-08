# Criterios de etiquetado

Se etiqueta por lo que el cliente necesita que se resuelva, no por la palabra que usa. Si pide dos cosas de categorías distintas, aplican las reglas de desempate.

## Categorías

- **billing**: dinero. Cobros, cargos duplicados o no reconocidos, facturas que Nubbix le emite al cliente, reintegros, medios de pago, pagos no acreditados, precio del plan que ya tiene.
- **technical**: algo del sistema no funciona. Errores, caídas, pantallas en blanco, lentitud, bugs, datos incorrectos, integraciones y sincronización (bancos, Mercado Pago, tiendas online), facturación electrónica que el cliente no puede emitir por un error.
- **account**: acceso e identidad. Login, contraseña, 2FA, recuperación de cuenta, usuarios y permisos, sesiones, datos o email del titular, titularidad, alta o baja de usuarios y de la cuenta.
- **other**: preventa y comercial (planes, módulos o descuentos que no tiene, cotizaciones), feedback, saludos, fuera de dominio, spam.

## Reglas de desempate

1. **Multi-intención:** gana lo que bloquea al cliente o la causa raíz. Ej.: "no abre el módulo de ventas desde el lunes y, además, pido que me devuelvan lo cobrado" → technical (la caída es la causa; el reintegro es consecuencia).
2. **Login:** error del sistema al loguearse (pantalla en blanco, error 500 o 503) → technical. Problema de credenciales o permisos (contraseña mal, falta un permiso) → account. Ej.: "al hacer clic en ingresar, la pantalla queda en blanco" → technical.
3. **Plan:** preguntar por un plan o módulo que no tiene → other. Cobro o precio del plan que ya tiene → billing. Ej.: "cuánto cuesta pasarme al plan Empresa" → other; "cuánto me cuesta mi plan actual por mes" → billing.
4. **Facturación electrónica:** la factura que el cliente emite a SUS clientes y falla → technical. La factura que Nubbix le emite al cliente → billing. Ej.: "la DGI rechaza el comprobante que emito a mi cliente" → technical; "Nubbix me emitió la factura de la suscripción con otro importe" → billing.

## Reglas generales

- Un reclamo por un cobro es billing, aunque sea por algo que el cliente no contrató. La regla 3 aplica a preguntas, no a reclamos.
- Un bloqueo causado por un pago no acreditado es billing: la causa raíz es el pago.
- Una sugerencia que describe algo que no funciona es technical.
- Un pedido de una función que no existe es other (feedback).
- Saludos, spam o preguntas sin relación con Nubbix son other, aunque el texto sea confuso.
- Un mensaje en otro idioma se etiqueta igual que en español.
- Si ninguna regla alcanza, anotar el caso como ambiguo en notes y revisarlo a mano. Ese "ambiguo" es una nota, no un tag: el tag `frontera` marca los casos que una regla sí resuelve.

## Tags

Los tags describen cada caso para leer el dataset y calcular su distribución. El runner no los usa. Los umbrales son fijos:

- **Longitud:** `largo` si tiene más de 250 caracteres; `corto` si tiene menos de 40.
- **Registro:** exactamente uno de `formal` o `informal`. `formal` si tiene una marca de cortesía ("Buenas tardes", "Buen día", "por favor", "agradecemos", "les pido", "quisiera", "gracias.", "please") y ninguna marca informal. `informal` en los demás casos. Marcas informales: tuteo o voseo ("sabés", "tenés", "entrá"), "hola", "oigan", "oye", modismos ("po", "encima", "la plata", "me sale", "saco", "ahorita") y mayúsculas sostenidas.
- **Mayúsculas:** `mayusculas` si al menos el 90 % de las letras están en mayúscula.
- **Ortografía:** `typo` si hay al menos un error de escritura en una palabra: tilde omitida o mal puesta, letra de más, de menos o cambiada, o palabra unida o separada mal ("POR QUE" en vez de "por qué"). La puntuación, las mayúsculas de inicio y los modismos no cuentan.
- **Tono:** `enojado` si el cliente expresa enojo o una queja fuerte ("esto es un robo", "abuso", "así no se puede trabajar").
- **Dominio:** `fuera_de_dominio` si no pide nada sobre Nubbix: saludo sin consulta, spam o temas ajenos al software.
- **Idioma:** `otro_idioma` si el texto no está en español.
- **Dificultad:** `multi_intencion` si la notes cita la regla 1. `frontera` si cita la regla 2, 3 o 4. Las reglas generales no marcan dificultad. `frontera` reemplaza al antiguo tag `ambiguo`.
- **Región:** exactamente uno de `regional_ar`, `regional_mx`, `regional_co`, `regional_cl` o `neutro`. Una marca regional es una palabra, expresión, saludo, institución (DIAN, ARCA, SII, CFDI o RFC) o lugar (Rosario, Mendoza) que identifica a un país. El tuteo, el voseo y las palabras que se usan en varios países ("la plata") no cuentan. Un lugar sí cuenta aunque el texto tutee: por eso t012 (Mendoza) queda `regional_ar`.

El holdout usa las mismas definiciones de `frontera`, `multi_intencion` y registro. Sus tags regionales no pasaron por estos criterios.
