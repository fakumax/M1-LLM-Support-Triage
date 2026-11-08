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
- Si ninguna regla alcanza, anotar el caso como ambiguo en notes y revisarlo a mano.
