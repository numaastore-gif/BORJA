// POST /api/checkout
// Crea una sesión de Stripe Checkout con los artículos de la cesta.
// Cada artículo es una configuración completa de pieza; el precio se recalcula
// aquí con los mismos datos que usa la web (api/_data.js, generado por
// tools/arko_data.py). Nunca se usa el precio que envía el navegador.
// Variables de entorno: STRIPE_SECRET_KEY, SITE_URL (p. ej. https://arko.studio)
import Stripe from 'stripe';
import DATA from './_data.js';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
const { lines: LINES, pricing: PRICING, catalog: CATALOG, filaments: FILAMENTS } = DATA;
const FIL = Object.fromEntries(FILAMENTS.map(f => [f.code, f]));
const TYPE_NAMES = { vase: 'Jarrón', lamp: 'Lámpara', planter: 'Maceta', tray: 'Bandeja', candle: 'Portavelas' };
const SHAPES = ['organica', 'columna', 'caliz', 'bulbo', 'cono', 'reloj'];
const TEXTURES = ['lisa', 'ondas', 'estrias', 'costillas', 'relieve'];

const int = (v, min, max) => Number.isInteger(v) && v >= min && v <= max;
const num = (v, min, max) => typeof v === 'number' && Number.isFinite(v) && v >= min && v <= max;
function validParams(p) {
  if (!p || !TYPE_NAMES[p.type] || !SHAPES.includes(p.shape) || !TEXTURES.includes(p.tex) || !LINES[p.line]) return false;
  if (!int(p.height, 4, 40) || !num(p.width, .7, 1.4) || !num(p.mouth, .5, 1.5) || !int(p.twist, -360, 360) || !int(p.sides, 3, 32)) return false;
  if (!num(p.texAmt, 0, 1) || !int(p.texN, 6, 40) || !int(p.seed, 1, 99999)) return false;
  const f1 = FIL[p.color]; if (!f1 || f1.line !== p.line) return false;
  if (p.mode === 'bicolor') { const f2 = FIL[p.color2]; if (p.line === 'gradient' || !f2 || f2.line !== p.line || !num(p.split, .15, .85)) return false; }
  else if (p.mode !== 'solid') return false;
  if (typeof p.engrave !== 'string' || p.engrave.length > 14 || /[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .,&'·-]/.test(p.engrave)) return false;
  if (p.watertight && !(p.type === 'vase' || p.type === 'planter')) return false;
  return true;
}
function priceOf(p) {
  let pr = PRICING.base[p.type] + PRICING.perCm[p.type] * p.height * p.width + LINES[p.line].fee;
  if (p.mode === 'bicolor') pr += PRICING.bicolor;
  if (p.watertight) pr += PRICING.watertight;
  if (p.engrave) pr += PRICING.engrave;
  return Math.round(pr);
}
function describe(p) {
  const f1 = FIL[p.color], f2 = FIL[p.color2];
  return [`${p.height} cm`, `${LINES[p.line].name} ${f1.name} (${f1.code})` + (p.mode === 'bicolor' ? ` + ${f2.name} (${f2.code})` : ''),
    p.watertight ? 'interior estanco' : '', p.engrave ? `grabado «${p.engrave}»` : ''].filter(Boolean).join(' · ');
}

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).json({ error: 'Usa POST' });
  const items = req.body?.items;
  if (!Array.isArray(items) || !items.length || items.length > 20) return res.status(400).json({ error: 'Cesta vacía o no válida' });

  const lineItems = [];
  let subtotal = 0;
  for (const it of items) {
    if (!int(it.qty, 1, 10) || !validParams(it.params)) return res.status(400).json({ error: 'Artículo no válido' });
    const p = it.params, model = CATALOG.find(m => m.id === it.model);
    const price = priceOf(p);
    subtotal += price * it.qty;
    lineItems.push({
      quantity: it.qty,
      price_data: {
        currency: 'eur', unit_amount: price * 100,
        product_data: {
          name: model ? `${model.name} ${model.code}` : `${TYPE_NAMES[p.type]} a medida`,
          description: describe(p),
          // La ficha completa viaja con el pedido para producción (Stripe admite 500 caracteres por valor)
          metadata: { modelo: model ? model.code : 'a_medida', filamento: p.color, filamento_2: p.mode === 'bicolor' ? p.color2 : '', params: JSON.stringify(p).slice(0, 499) },
        },
      },
    });
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
    cancel_url: `${process.env.SITE_URL}/taller.html`,
  });
  res.status(200).json({ url: session.url });
}
