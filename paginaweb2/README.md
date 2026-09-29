# ARKO

Tienda de objetos impresos en 3D con estética de brutalismo arquitectónico.
`index.html` es la web completa (HTML + CSS + JS, Three.js desde cdnjs).
`api/checkout.js` es la única pieza de servidor: crea el pago en Stripe.

## Qué puede hacer el cliente
- Diseñar su pieza en el **Taller**: tipología, altura, torsión, lados, ondulación y seed.
- Elegir **color** (10 colores de filamento o un color a medida, +8 €) y **acabado**
  (mate, seda +6 €, piedra +9 €). La vista 3D cambia en directo.
- Partir de una pieza de la **Colección** con «Personalizar».
- Ver el plazo: **7 días de preparación + envío (24–72 h laborables)**, con fechas.
- Añadir a la **cesta** (se guarda en su navegador) y pagar con tarjeta.

## Precios (editar en los dos sitios: `PRICING` en index.html y en api/checkout.js)
| Tipo       | Base | €/cm |
|------------|------|------|
| Jarrón     | 29   | 1,2  |
| Lámpara    | 59   | 2,5  |
| Maceta     | 25   | 1,3  |
| Bandeja    | 22   | 1,6  |
| Portavelas | 14   | 1,0  |

Envío 6,90 €, gratis desde 100 €. Son valores de partida: ajústalos a tus costes.

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
