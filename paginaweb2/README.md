# ARKO

Tienda de objetos impresos en 3D con estética de brutalismo arquitectónico.

## Estructura
| Archivo | Página |
|---|---|
| `index.html` | Inicio: arco con la pieza en 3D, cuatro "puertas" a las salas, destacadas y cuaderno |
| `coleccion.html` | Los cuatro modelos + acceso a «Crea el tuyo» |
| `pieza.html#anfora` | Ficha de cada modelo: 3D con lupa, cambio de color, ficha técnica, sección constructiva |
| `taller.html` | Configurador completo (ver abajo) |
| `proceso.html` | Las cuatro fases de fabricación |
| `estudio.html` | Manifiesto, cifras y cuaderno |
| `assets/arko.css` | Estilos compartidos (prefijo `pw-`) |
| `assets/arko.js` | JS compartido: cabecera, pie, cesta, motor 3D y módulos de cada página |
| `assets/arko-data.js` | Datos generados por `tools/arko_data.py` |
| `api/checkout.js` | Única pieza de servidor: crea el pago en Stripe |

- La cabecera, el pie, la cesta y el cursor los inyecta `arko.js`, así se editan en un solo sitio.
- Los modelos, precios y colores salen de `tools/arko_data.py` (ver «Datos»).
- Entre páginas hay una transición de "desencofrado" (View Transitions; en navegadores sin
  soporte la navegación es normal).
- "Personalizar" lleva la pieza al taller guardándola un momento en el navegador.

## Negocio: cuatro modelos fijos + crea el tuyo
Los modelos de la casa son **Ánfora**, **Monolito**, **Estrato** (lámpara) y **Onda** (maceta).
Cada uno se puede pedir tal cual, cambiarle el color en su ficha o llevarlo al taller.

En el **Taller** el cliente elige:
- Punto de partida: uno de los cuatro modelos o desde cero.
- Tipología: jarrón, lámpara, maceta, bandeja, portavelas.
- Silueta (jarrones): orgánica, columna, cáliz, bulbo, cono, reloj.
- Medidas: altura, anchura y boca.
- Superficie: lisa, ondas, estrías, costillas o relieve, con intensidad y densidad;
  además torsión, número de lados y variación (seed).
- Filamento Bambu Lab: PLA Matte, Basic, Silk+, Marble, Wood, Translucent y Basic Gradient
  (94 colores oficiales con su código).
- Bicolor por capas (cambio de filamento en una capa exacta con el AMS).
- Extras: interior estanco para flores frescas y grabado en la base.
- Plazo: **7 días de preparación + envío (24–72 h laborables)**, con fechas.

## Datos: una sola fuente
`tools/arko_data.py` contiene precios, líneas de filamento, colores y los cuatro modelos.
Al ejecutarlo genera `assets/arko-data.js` (web) y `api/_data.js` (pago), así que la web y el
servidor nunca se desincronizan:

    python3 tools/arko_data.py

Los colores son los oficiales de Bambu Lab tal como los publica Bambu Studio
(`resources/profiles/BBL/filament/filaments_color_codes.json`): código, nombre en español y hex.
Coinciden con las tablas de hex que Bambu publica en su tienda.

## Realismo y fidelidad de color
- Render con material físico por línea (mate, satinado, seda con reflejo metálico, moteado de
  mármol, fibra de madera, translúcido), entorno de estudio con reflejos, sombra suave y sombra
  de contacto.
- Capas reales de 0,2 mm (normal map): se ven al acercar la lupa.
- Sin curva de tono: la luz está calibrada para que la cara frontal reproduzca el hex del
  filamento (medido: Terracota #B15533 → 175/89/61; Gris ceniza #9B9EA0 → 154/156/157).
- Las fotos de las tarjetas se renderizan con el mismo motor y material que el taller.
- Límites honestos: cada pantalla muestra el color un poco distinto; Bambu da #FFFFFF y #000000
  como hex nominales de sus blancos y negros (en la pieza real el negro mate se ve gris muy
  oscuro, como en el render); en los degradados la transición real depende del tramo del rollo.

## Publicar con pago real (sin Shopify)
1. Crea una cuenta en Stripe y activa los pagos (datos fiscales y cuenta bancaria).
2. Sube esta carpeta a Vercel (plan gratuito). `api/checkout.js` se convierte en `/api/checkout`.
3. En Vercel añade las variables `STRIPE_SECRET_KEY` y `SITE_URL` (tu dominio).
4. Conecta el dominio (p. ej. arko.studio si está libre).
5. Prueba con la clave de test de Stripe y la tarjeta 4242 4242 4242 4242.

Cada pedido llega a tu panel de Stripe con la ficha completa de la pieza
(`params`: forma, seed, color y acabado) para poder imprimirla tal cual.

### Siguientes pasos recomendados
- Webhook `checkout.session.completed` que te mande un correo o guarde el pedido
  en una hoja de cálculo con la ficha de impresión.
- Facturas automáticas (Stripe Invoicing o tu programa de facturación).
- Textos legales obligatorios en España: aviso legal, privacidad, cookies,
  condiciones de venta. Ojo: el derecho de desistimiento no aplica a productos
  personalizados, pero debe indicarse en las condiciones.
