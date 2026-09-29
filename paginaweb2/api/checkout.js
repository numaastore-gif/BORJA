// POST /api/checkout
// Crea una sesión de Stripe Checkout con los artículos de la cesta.
// El precio se recalcula aquí: nunca se usa el que envía el navegador.
// Variables de entorno: STRIPE_SECRET_KEY, SITE_URL (p. ej. https://arko.studio)
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

// Mantener igual que PRICING / FINISHES / COLORS / CATALOG en assets/arko.js
const PRICING = {
  base: { vase: 29, lamp: 59, planter: 25, tray: 22, candle: 14 },
  perCm: { vase: 1.2, lamp: 2.5, planter: 1.3, tray: 1.6, candle: 1 },
  customColor: 8,
  shipping: 6.9, freeShippingFrom: 100,
};
const FINISHES = { mate: 0, seda: 6, piedra: 9 };
const COLOR_IDS = ['cal', 'arena', 'hormigon', 'salvia', 'oliva', 'arcilla', 'cognac', 'pizarra', 'basalto', 'carbon', 'custom'];
const TYPE_NAMES = { vase: 'Jarrón', lamp: 'Lámpara', planter: 'Maceta', tray: 'Bandeja', candle: 'Portavelas' };
// Piezas fijas de la colección (código → nombre y precio)
const CATALOG = {
  'V—042': ['Jarrón torsión hexagonal', 48], 'L—017': ['Lámpara estrato', 129], 'P—023': ['Portavelas pentágono', 24],
  'B—008': ['Bandeja curva de nivel', 36], 'M—031': ['Maceta onda', 42], 'V—077': ['Jarrón monolito', 64],
  'L—005': ['Lámpara espiral doce', 149], 'M—012': ['Maceta octógono', 38],
};

const int = (v, min, max) => Number.isInteger(v) && v >= min && v <= max;
function validParams(p) {
  return p && TYPE_NAMES[p.type] && int(p.height, 4, 40) && int(p.twist, -360, 360) && int(p.sides, 3, 32) &&
    typeof p.wave === 'number' && p.wave >= 0 && p.wave <= 1 && int(p.seed, 1, 99999) &&
    FINISHES[p.finish] !== undefined && COLOR_IDS.includes(p.colorId) && /^#[0-9a-f]{6}$/i.test(p.color);
}
const priceOf = p => Math.round(PRICING.base[p.type] + PRICING.perCm[p.type] * p.height + FINISHES[p.finish] + (p.colorId === 'custom' ? PRICING.customColor : 0));

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Usa POST' });
  const items = req.body?.items;
  if (!Array.isArray(items) || !items.length || items.length > 20) return res.status(400).json({ error: 'Cesta vacía o no válida' });

  const lineItems = [];
  let subtotal = 0;
  for (const it of items) {
    if (!int(it.qty, 1, 10)) return res.status(400).json({ error: 'Cantidad no válida' });
    let name, price, metadata;
    if (it.kind === 'catalog' && CATALOG[it.code]) {
      [name, price] = CATALOG[it.code];
      metadata = { tipo: 'coleccion', codigo: it.code };
    } else if (it.kind === 'custom' && validParams(it.params)) {
      const p = it.params;
      name = `${TYPE_NAMES[p.type]} a medida · seed ${p.seed}`;
      price = priceOf(p);
      // La ficha completa viaja con el pedido para producción
      metadata = { tipo: 'a_medida', params: JSON.stringify(p).slice(0, 490) };
    } else return res.status(400).json({ error: 'Artículo no válido' });
    subtotal += price * it.qty;
    lineItems.push({ quantity: it.qty, price_data: { currency: 'eur', unit_amount: price * 100, product_data: { name, metadata } } });
  }

  const shipping = subtotal >= PRICING.freeShippingFrom ? 0 : Math.round(PRICING.shipping * 100);
  const session = await stripe.checkout.sessions.create({
    mode: 'payment',
    locale: 'es',
    line_items: lineItems,
    shipping_address_collection: { allowed_countries: ['ES', 'PT'] },
    phone_number_collection: { enabled: true },
    shipping_options: [{
      shipping_rate_data: {
        type: 'fixed_amount',
        fixed_amount: { amount: shipping, currency: 'eur' },
        display_name: 'Preparación 7 días + envío 24–72 h',
        delivery_estimate: { minimum: { unit: 'business_day', value: 6 }, maximum: { unit: 'business_day', value: 8 } },
      },
    }],
    success_url: `${process.env.SITE_URL}/?pedido=ok`,
    cancel_url: `${process.env.SITE_URL}/#taller`,
  });
  res.status(200).json({ url: session.url });
}
