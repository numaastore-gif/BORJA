/* =====================================================================
   ARKO — JS compartido por todas las páginas
   Cada página marca <body data-page="…"> y solo se inicializan los
   módulos cuyos elementos existen en ella.
   00 utilidades · 00b tienda · 00c catálogo · 00d cromo común ·
   01 forma · 02 escena 3D · 03 preloader · 04 cursor · 05 header ·
   06 reveal + fraguado + luz rasante · 07 hero + franja · 08 proceso ·
   09 taller · 10 colección + pieza + inicio · 10b cesta · 11 manifiesto ·
   12 cifras · 13 newsletter · 14 footer · 15 arranque
   ===================================================================== */
(function () {
'use strict';

/* ---------- 00. UTILIDADES ---------- */
const PW = {
  reduced: matchMedia('(prefers-reduced-motion: reduce)').matches,
  fine: matchMedia('(hover: hover) and (pointer: fine)').matches,
  isMobile: () => innerWidth < 640,
  hasThree: typeof window.THREE !== 'undefined',
};
const $ = (s, c = document) => c.querySelector(s);
const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
const easeOutExpo = t => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t));
const easeInOut = t => (t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const pad = (n, l) => String(n).padStart(l, '0');
const fmt = (n, d = 0) => { const [i, f] = Math.abs(n).toFixed(d).split('.'); return (n < 0 ? '-' : '') + i.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (f ? ',' + f : ''); };
function mulberry32(a) { return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function watchVisible(el, cb, margin = '80px') { if (!el) return; const io = new IntersectionObserver(es => es.forEach(e => cb(e.isIntersecting)), { rootMargin: margin }); io.observe(el); return io; }
const bus = new EventTarget();
const emit = (n, d) => bus.dispatchEvent(new CustomEvent(n, { detail: d }));
const on = (n, fn) => bus.addEventListener(n, e => fn(e.detail));

/* ---------- 00b. TIENDA: colores, acabados, precios y plazos ----------
   Mantener PRICING igual que en api/checkout.js: el servidor recalcula
   el precio y nunca se fía del que envía el navegador. */
const COLORS = [
  { id: 'cal', name: 'Cal', hex: '#E4DCCD' },
  { id: 'arena', name: 'Arena', hex: '#CDBEA5' },
  { id: 'hormigon', name: 'Hormigón', hex: '#A9A298' },
  { id: 'salvia', name: 'Salvia', hex: '#9AA290' },
  { id: 'oliva', name: 'Oliva', hex: '#7A7658' },
  { id: 'arcilla', name: 'Arcilla', hex: '#B37E5A' },
  { id: 'cognac', name: 'Coñac', hex: '#9C5F38' },
  { id: 'pizarra', name: 'Pizarra', hex: '#5E6870' },
  { id: 'basalto', name: 'Basalto', hex: '#4C4742' },
  { id: 'carbon', name: 'Carbón', hex: '#262422' },
];
const FINISHES = { mate: { name: 'Mate', fee: 0 }, seda: { name: 'Seda', fee: 6 }, piedra: { name: 'Piedra', fee: 9 } };
const TYPE_NAMES = { vase: 'Jarrón', lamp: 'Lámpara', planter: 'Maceta', tray: 'Bandeja', candle: 'Portavelas' };
const PRICING = {
  base: { vase: 29, lamp: 59, planter: 25, tray: 22, candle: 14 },   // € de partida
  perCm: { vase: 1.2, lamp: 2.5, planter: 1.3, tray: 1.6, candle: 1 }, // € por cm de altura
  customColor: 8,
  shipping: 6.9, freeShippingFrom: 100,
  prepDays: 7, shipMin: 1, shipMax: 3, // 7 días naturales + 1–3 laborables
};
function priceOf(p) {
  const base = PRICING.base[p.type] ?? 29, cm = PRICING.perCm[p.type] ?? 1.2;
  return Math.round(base + cm * p.height + (FINISHES[p.finish]?.fee || 0) + (p.colorId === 'custom' ? PRICING.customColor : 0));
}
const shippingOf = subtotal => (subtotal === 0 ? 0 : subtotal >= PRICING.freeShippingFrom ? 0 : PRICING.shipping);
const money = n => (Number.isInteger(n) ? n : n.toFixed(2).replace('.', ',')) + ' €';
function deliveryWindow(from = new Date()) {
  const start = new Date(from); start.setDate(start.getDate() + PRICING.prepDays);
  const add = (d, n) => { const x = new Date(d); while (n > 0) { x.setDate(x.getDate() + 1); if (x.getDay() !== 0 && x.getDay() !== 6) n--; } return x; };
  const f = d => d.toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric', month: 'short' }).replace(',', '');
  return `Si lo pides hoy, llega entre el ${f(add(start, PRICING.shipMin))} y el ${f(add(start, PRICING.shipMax))}.`;
}

/* ---------- 00c. CATÁLOGO ----------
   Fuente única de las piezas de la colección (los códigos deben coincidir
   con CATALOG en api/checkout.js). */
const CATALOG = [
  { id: 'v042', code: 'V—042', name: 'Jarrón torsión hexagonal', price: 48, tone: 'hormigon', tag: 'Nuevo · 1/50', layer: '0,2 mm', time: '14 h 32', material: 'PLA hormigón',
    form: { type: 'vase', seed: 42, height: 28, twist: 140, sides: 6, wave: .1 },
    desc: 'Seis caras que giran 140° de la base a la boca. La luz lateral dibuja una arista distinta a cada hora del día.' },
  { id: 'l017', code: 'L—017', name: 'Lámpara estrato', price: 129, tone: 'hueso', tag: 'Luz cálida', layer: '0,16 mm', time: '21 h 08', material: 'PETG ópalo',
    form: { type: 'lamp', seed: 17, height: 22, twist: 40, sides: 32, wave: .55 },
    desc: 'Una pantalla que se abre como un arco invertido. Las ondas de la superficie tamizan la luz en franjas suaves sobre la pared.' },
  { id: 'p023', code: 'P—023', name: 'Portavelas pentágono', price: 24, tone: 'arcilla', tag: 'Set de 3', layer: '0,2 mm', time: '2 h 45', material: 'PLA arcilla',
    form: { type: 'candle', seed: 23, height: 9, twist: -60, sides: 5, wave: .2 },
    desc: 'Tres piezas bajas de cinco lados, con un leve giro. Pensadas para agruparse en una mesa o repartirse por una estantería.' },
  { id: 'b008', code: 'B—008', name: 'Bandeja curva de nivel', price: 36, tone: 'carbon', tag: 'Topografía', layer: '0,2 mm', time: '6 h 12', material: 'PLA basalto',
    form: { type: 'tray', seed: 8, height: 6, twist: 0, sides: 9, wave: .35 },
    desc: 'Una bandeja baja cuyo borde ondula como un mapa topográfico. Para llaves, fruta o nada en absoluto.' },
  { id: 'm031', code: 'M—031', name: 'Maceta onda', price: 42, tone: 'arena', tag: 'Con drenaje', layer: '0,24 mm', time: '11 h 50', material: 'PLA arena',
    form: { type: 'planter', seed: 31, height: 16, twist: 20, sides: 32, wave: .8 },
    desc: 'Pared ondulada de arriba abajo, como un encofrado de chapa. Lleva orificio de drenaje y platillo a juego.' },
  { id: 'v077', code: 'V—077', name: 'Jarrón monolito', price: 64, tone: 'carbon', tag: 'Últimas 6', layer: '0,2 mm', time: '18 h 04', material: 'PLA basalto',
    form: { type: 'vase', seed: 77, height: 34, twist: -220, sides: 4, wave: 0 },
    desc: 'Una columna de cuatro caras retorcida 220°. Pesa a la vista y se sostiene sola en el suelo o sobre un aparador.' },
  { id: 'l005', code: 'L—005', name: 'Lámpara espiral doce', price: 149, tone: 'arena', tag: 'E27 · LED', layer: '0,16 mm', time: '26 h 40', material: 'PETG ópalo',
    form: { type: 'lamp', seed: 5, height: 30, twist: 180, sides: 12, wave: .15 },
    desc: 'Doce caras que dan media vuelta completa. Incluye portalámparas E27, cable textil y bombilla LED cálida.' },
  { id: 'm012', code: 'M—012', name: 'Maceta octógono', price: 38, tone: 'arcilla', tag: 'Exterior', layer: '0,28 mm', time: '9 h 22', material: 'PLA arcilla',
    form: { type: 'planter', seed: 12, height: 20, twist: -30, sides: 8, wave: .3 },
    desc: 'Ocho caras escalonadas con un giro contenido. Material resistente a la intemperie para terraza o balcón.' },
];
const FAMILIES = { vase: 'Jarrones', lamp: 'Lámparas', planter: 'Macetas', tray: 'Bandejas', candle: 'Portavelas' };
const TONE_NAMES = { arcilla: 'Arcilla', hormigon: 'Hormigón', arena: 'Arena', carbon: 'Basalto', hueso: 'Cal' };
const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* sin almacenamiento */ } },
  del(k) { try { localStorage.removeItem(k); } catch (e) { /* sin almacenamiento */ } },
};

/* ---------- 00d. CROMO COMÚN: cabecera, pie, cesta y cursor ----------
   Se inyectan en cada página para no repetir el marcado. */
const CHROME = {
  header: `
  <a class="pw-header__logo" href="index.html" aria-label="ARKO, inicio">ARKO</a>
  <nav class="pw-header__nav" id="pw-nav" aria-label="Principal">
    <a href="coleccion.html" data-nav="coleccion">Colección</a>
    <a href="taller.html" data-nav="taller">Taller</a>
    <a href="proceso.html" data-nav="proceso">Proceso</a>
    <a href="estudio.html" data-nav="estudio">Estudio</a>
    <button class="pw-header__cart" type="button">Cesta (<span id="pw-cart-count">0</span>)</button>
  </nav>
  <div class="pw-header__status">
    <span><span class="pw-header__pulse" aria-hidden="true"></span><span class="pw-header__label">Piezas generadas hoy </span><b id="pw-gen-count">0000</b></span>
    <span class="pw-header__clock">BCN <b id="pw-clock">00:00:00</b></span>
  </div>
  <button class="pw-header__menu" type="button" aria-expanded="false" aria-controls="pw-nav">Menú</button>`,
  footer: `
  <div class="pw-footer__cols">
    <div class="pw-footer__col"><h4>Tienda</h4><ul><li><a href="coleccion.html#jarrones">Jarrones</a></li><li><a href="coleccion.html#lamparas">Lámparas</a></li><li><a href="coleccion.html#macetas">Macetas</a></li><li><a href="coleccion.html#bandejas">Bandejas</a></li></ul></div>
    <div class="pw-footer__col"><h4>Estudio</h4><ul><li><a href="taller.html">Taller</a></li><li><a href="proceso.html">Proceso</a></li><li><a href="estudio.html">Manifiesto</a></li><li><a href="estudio.html#cifras">Cifras</a></li></ul></div>
    <div class="pw-footer__col"><h4>Social</h4><ul><li><a href="#">Instagram</a></li><li><a href="#">Pinterest</a></li><li><a href="#">Printables</a></li></ul></div>
    <div class="pw-footer__col"><h4>Pedidos</h4><ul><li>Preparación 7 días</li><li>Envío 24–72 h</li><li><a href="#">Devoluciones</a></li><li><a href="#">Privacidad</a></li></ul></div>
    <div class="pw-footer__col pw-footer__coords"><h4>Coordenadas</h4><b>41.3874° N · 2.1686° E</b>Taller · Barcelona<br>Lunes a viernes · 10:00–19:00<br>hola@arko.studio</div>
  </div>
  <span class="pw-footer__brand" aria-hidden="true">ARKO</span>
  <div class="pw-footer__base"><span>© <span data-year>2026</span> ARKO · Forma generada. Materia impresa.</span><span>Hormigón, luz y filamento</span></div>`,
  cart: `
  <div class="pw-cart-veil" data-cart-close hidden></div>
  <aside class="pw-cart" id="pw-cart" aria-label="Cesta" aria-hidden="true" tabindex="-1">
    <header class="pw-cart__head"><h2 class="pw-cart__title">Cesta</h2><button class="pw-cart__close" type="button" data-cart-close>Cerrar</button></header>
    <div class="pw-cart__body"><p class="pw-cart__empty">Tu cesta está vacía. Diseña una pieza en el taller o elige una de la colección.</p><ul class="pw-cart__list"></ul></div>
    <footer class="pw-cart__foot">
      <dl class="pw-cart__totals">
        <div><dt>Subtotal</dt><dd data-cart="subtotal">0 €</dd></div>
        <div><dt>Envío</dt><dd data-cart="shipping">—</dd></div>
        <div class="pw-cart__total"><dt>Total (IVA incl.)</dt><dd data-cart="total">0 €</dd></div>
      </dl>
      <p class="pw-cart__eta"><b>7 días de preparación + envío.</b> <span data-cart="eta"></span></p>
      <button class="pw-btn pw-cart__pay" type="button" data-cart-pay>Pagar con tarjeta <span class="pw-btn__arrow" aria-hidden="true">→</span></button>
      <p class="pw-cart__msg" aria-live="polite"></p>
    </footer>
  </aside>`,
  cursor: `<span class="pw-cursor__ring"></span><span class="pw-cursor__dot"></span><span class="pw-cursor__label"></span>`,
  preloader: `<div class="pw-preloader__log"></div><div class="pw-preloader__row"><div class="pw-preloader__bar"><span></span></div><div class="pw-preloader__pct">0%</div></div>`,
};
function injectChrome(page) {
  const header = document.createElement('header'); header.className = 'pw-header'; header.innerHTML = CHROME.header;
  document.body.prepend(header);
  const skip = document.createElement('a'); skip.className = 'pw-skip'; skip.href = '#contenido'; skip.textContent = 'Saltar al contenido';
  document.body.prepend(skip);
  const cur = document.createElement('div'); cur.className = 'pw-cursor is-hidden'; cur.setAttribute('aria-hidden', 'true'); cur.innerHTML = CHROME.cursor;
  document.body.append(cur);
  const footer = document.createElement('footer'); footer.className = 'pw-footer'; footer.innerHTML = CHROME.footer;
  document.body.append(footer);
  document.body.insertAdjacentHTML('beforeend', CHROME.cart);
  const active = page === 'pieza' ? 'coleccion' : page;
  const link = $(`[data-nav="${active}"]`, header); if (link) link.setAttribute('aria-current', 'page');
}
// Lleva una configuración al taller (en otra página)
function openInTaller(params) {
  if (document.body.dataset.page === 'taller') { emit('lab:load', params); return; }
  store.set('arko-taller', params);
  location.href = 'taller.html';
}
function catalogParams(item) {
  const c = COLORS.find(x => x.name === TONE_NAMES[item.tone]) || COLORS[0];
  return Object.assign({}, item.form, { colorId: c.id, color: c.hex, colorName: c.name, finish: 'mate' });
}
function addCatalogItem(item) {
  emit('cart:add', { key: item.code, kind: 'catalog', code: item.code, name: `${item.name} ${item.code}`, desc: `${item.form.height} cm · ${TONE_NAMES[item.tone]} · Mate`, price: item.price, color: TONES[item.tone][1] });
}

/* Texturas de muro generadas en canvas (ruido periódico = teselas sin costuras).
   Sustituyen a las SVG de :root, que algunos navegadores rasterizan con cortes. */
function makeWallTextures() {
  const periodic = (gx, gy, seed) => {
    const r = mulberry32(seed), g = Array.from({ length: gx * gy }, () => r());
    return (u, v) => { // u,v ∈ [0,1)
      const x = u * gx, y = v * gy, x0 = Math.floor(x), y0 = Math.floor(y), fx = x - x0, fy = y - y0;
      const sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
      const at = (i, j) => g[((j % gy + gy) % gy) * gx + ((i % gx + gx) % gx)];
      return lerp(lerp(at(x0, y0), at(x0 + 1, y0), sx), lerp(at(x0, y0 + 1), at(x0 + 1, y0 + 1), sx), sy);
    };
  };
  const paint = (size, fn) => {
    const cv = document.createElement('canvas'); cv.width = cv.height = size;
    const ctx = cv.getContext('2d'), img = ctx.createImageData(size, size), d = img.data;
    for (let y = 0; y < size; y++) for (let x = 0; x < size; x++) { const [r, g, b, a] = fn(x / size, y / size), i = (y * size + x) * 4; d[i] = r; d[i + 1] = g; d[i + 2] = b; d[i + 3] = a; }
    ctx.putImageData(img, 0, 0);
    return `url(${cv.toDataURL('image/png')})`;
  };
  const oct = [periodic(4, 4, 3), periodic(8, 8, 5), periodic(16, 16, 9), periodic(32, 32, 13)];
  const fbm = (u, v) => oct[0](u, v) * .5 + oct[1](u, v) * .27 + oct[2](u, v) * .15 + oct[3](u, v) * .08;
  const mottle = paint(384, (u, v) => { const n = (fbm(u, v) - .5) * 2.2; return n > 0 ? [52, 44, 36, clamp(n * 70, 0, 58)] : [255, 250, 240, clamp(-n * 70, 0, 52)]; });
  const rnd = mulberry32(21);
  const grain = paint(256, () => { const n = rnd(); return n > .5 ? [40, 34, 28, (n - .5) * 70] : [255, 250, 240, (.5 - n) * 44]; });
  const w1 = periodic(64, 3, 17), w2 = periodic(160, 6, 19);
  const wood = paint(384, (u, v) => { const n = (w1(u, v) * .65 + w2(u, v) * .35 - .5) * 2; return n > 0 ? [46, 38, 30, clamp(n * 75, 0, 62)] : [255, 250, 240, clamp(-n * 50, 0, 40)]; });
  const root = document.documentElement.style;
  root.setProperty('--pw-tx-mottle', mottle); root.setProperty('--pw-tx-grain', grain); root.setProperty('--pw-tx-wood', wood);
}

/* ---------- 01. NÚCLEO DE FORMA ----------
   params: { type, height (cm), twist (°), sides (3–32; 32 = redondo), wave (0–1), seed } */
const PWForm = {
  CODES: { vase: 'V', lamp: 'L', planter: 'M', tray: 'B', candle: 'P' },
  coeffs(seed) {
    const r = mulberry32((seed * 9301 + 49297) | 0);
    return { bc: .22 + r() * .32, bw: .13 + r() * .15, bulb: .26 + r() * .24, lip: r() * .16, a2: .02 + r() * .05, f2: 1 + r() * 2.6, p2: r(), wf: 3 + Math.floor(r() * 6), wp: r() * 6.283, k: r() };
  },
  radius(type, t, c) {
    const rip = c.a2 * Math.sin(Math.PI * 2 * (c.f2 * t + c.p2));
    switch (type) {
      case 'lamp':    return .2 + .88 * Math.pow(t, 1.15 + c.k * 1.6) + rip * .8 + .05 * smooth(.9, 1, t);
      case 'planter': return .52 + .3 * t + rip * .7 + .06 * smooth(.88, 1, t) - .05 * (1 - smooth(0, .08, t));
      case 'tray':    return .82 + .2 * smooth(0, 1, t) + rip * .25;
      case 'candle':  return .36 + .1 * Math.sin(Math.PI * t) - .06 * t + rip * .6;
      default: { const bulb = c.bulb * Math.exp(-((t - c.bc) ** 2) / (2 * c.bw * c.bw)); return Math.max(.12, .27 + bulb + c.lip * smooth(.78, 1, t) + rip); }
    }
  },
  point(p, c, t, phi, out) {
    const H = p.height / 10;
    let r = PWForm.radius(p.type, t, c);
    if (p.sides < 32) { const seg = (Math.PI * 2) / p.sides; const a = ((phi % seg) + seg) % seg - seg / 2; r *= Math.cos(seg / 2) / Math.cos(a); }
    r *= 1 + p.wave * .14 * Math.sin(phi * c.wf + t * Math.PI * 4 + c.wp);
    const ang = phi + (p.twist * Math.PI / 180) * t;
    out[0] = r * Math.cos(ang); out[1] = t * H; out[2] = r * Math.sin(ang);
    return out;
  },
  code(p) { return `${PWForm.CODES[p.type] || 'O'}—${pad(p.seed, 5)}`; },
};

/* ---------- 02. ESCENA 3D ----------
   Pieza sobre pedestal de hormigón, luz cálida lateral con sombra suave,
   material mineral con líneas de capa y construcción capa a capa. */
function buildFormGeometry(p, resU, resV) {
  const n = p.sides, U = n < 32 ? n * Math.max(1, Math.ceil(resU / n)) : resU, V = resV;
  const count = U * (V + 1) + 1, geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
  geo.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(count * 2), 2));
  const idx = [];
  for (let j = 0; j < V; j++) for (let i = 0; i < U; i++) {
    const a = j * U + i, b = j * U + ((i + 1) % U), c = (j + 1) * U + i, d = (j + 1) * U + ((i + 1) % U);
    idx.push(a, c, b, b, c, d);
  }
  const center = U * (V + 1);
  for (let i = 0; i < U; i++) idx.push(center, i, (i + 1) % U);
  geo.setIndex(idx);
  geo.userData = { U, V, sides: n };
  fillFormPositions(geo, p);
  return geo;
}
function fillFormPositions(geo, p) {
  const { U, V } = geo.userData, c = PWForm.coeffs(p.seed), H = p.height / 10;
  const pos = geo.attributes.position.array, uv = geo.attributes.uv.array, tmp = [0, 0, 0];
  let k = 0, q = 0;
  for (let j = 0; j <= V; j++) {
    const t = j / V;
    for (let i = 0; i < U; i++) {
      PWForm.point(p, c, t, (i / U) * Math.PI * 2, tmp);
      pos[k++] = tmp[0]; pos[k++] = tmp[1] - H / 2; pos[k++] = tmp[2];
      uv[q++] = (i / U) * 3; uv[q++] = t * H * 1.15;
    }
  }
  pos[k++] = 0; pos[k++] = -H / 2; pos[k++] = 0; uv[q++] = 0; uv[q++] = 0;
  geo.attributes.position.needsUpdate = true; geo.attributes.uv.needsUpdate = true;
  geo.computeVertexNormals(); geo.computeBoundingSphere();
}
// Textura mineral con líneas de capa (64 capas por tesela)
function makeClayTexture() {
  const w = 128, h = 256, cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  const ctx = cv.getContext('2d'), img = ctx.createImageData(w, h), d = img.data, rnd = mulberry32(7);
  for (let y = 0; y < h; y++) {
    const layer = y % 4 === 0 ? -18 : y % 4 === 1 ? 7 : 0, band = Math.sin(y * .07) * 3;
    for (let x = 0; x < w; x++) { const v = clamp(228 + layer + band + (rnd() - .5) * 20, 0, 255), i = (y * w + x) * 4; d[i] = d[i + 1] = d[i + 2] = v; d[i + 3] = 255; }
  }
  ctx.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.encoding = THREE.sRGBEncoding; return t;
}
// Hormigón del pedestal: grano + poros
function makeConcreteTexture() {
  const s = 256, cv = document.createElement('canvas'); cv.width = cv.height = s;
  const ctx = cv.getContext('2d'), img = ctx.createImageData(s, s), d = img.data, rnd = mulberry32(11);
  for (let i = 0; i < s * s; i++) { const v = 222 + (rnd() - .5) * 26; d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = v; d[i * 4 + 3] = 255; }
  ctx.putImageData(img, 0, 0);
  for (let i = 0; i < 90; i++) { ctx.fillStyle = `rgba(90,80,70,${.25 + rnd() * .4})`; ctx.beginPath(); ctx.ellipse(rnd() * s, rnd() * s, .6 + rnd() * 2, .6 + rnd() * 1.6, 0, 0, 6.3); ctx.fill(); }
  const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(3, 1); t.encoding = THREE.sRGBEncoding; return t;
}
const lin = hex => new THREE.Color(hex).convertSRGBToLinear();

class FormStage {
  constructor(canvas, opts) {
    this.canvas = canvas;
    this.o = Object.assign({ tone: 0xC9BBA6, line: 0x2A2927, accent: 0x9C5F38, plinth: 0xBDB5A9, resU: 96, resV: 120, autoRotate: .16, elev: .14, plinthH: .9, key: [-3.4, 4.8, 3.4] }, opts);
    this.p = Object.assign({}, opts.params);
    this.running = false; this.visible = false; this.view = 'solid';
    this.rotY = .5; this.rotVel = 0; this.elev = this.o.elev; this.targetElev = this.o.elev;
    this.build = null; this.onFrame = null; this.target = new THREE.Vector3();

    const r = this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    r.setPixelRatio(Math.min(devicePixelRatio || 1, PW.isMobile() ? 1.5 : 2));
    r.setClearColor(0x000000, 0);
    r.outputEncoding = THREE.sRGBEncoding;
    r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = 1.08;
    r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
    r.localClippingEnabled = true;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(28, 1, .1, 100);
    this.scene.add(new THREE.HemisphereLight(lin(0xFFF3E2), lin(0x6A5E52), .75));
    const key = this.key = new THREE.DirectionalLight(lin(0xFFDDB6), 2.7);
    key.position.set(...this.o.key); key.castShadow = true;
    key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -.0006; key.shadow.normalBias = .02; key.shadow.radius = 6;
    this.scene.add(key);
    const fill = new THREE.DirectionalLight(lin(0xDCE2E8), .4); fill.position.set(4, 1.5, 2.5); this.scene.add(fill);

    this.plane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 999);
    const clay = makeClayTexture();
    this.matSolid = new THREE.MeshStandardMaterial({ color: lin(this.o.tone), map: clay, bumpMap: clay, bumpScale: .022, roughness: .95, metalness: 0, side: THREE.DoubleSide, clippingPlanes: [this.plane] });
    this.matWire = new THREE.MeshBasicMaterial({ color: lin(this.o.line), wireframe: true, transparent: true, opacity: .5, clippingPlanes: [this.plane] });
    this.matLayers = new THREE.LineBasicMaterial({ color: lin(this.o.line), transparent: true, opacity: .75, clippingPlanes: [this.plane] });

    this.group = new THREE.Group(); this.scene.add(this.group);
    this.mesh = new THREE.Mesh(undefined, this.matSolid); this.mesh.castShadow = true; this.mesh.receiveShadow = true; this.group.add(this.mesh);
    this.layers = new THREE.LineSegments(new THREE.BufferGeometry(), this.matLayers); this.layers.visible = false; this.group.add(this.layers);
    this.ring = new THREE.LineLoop(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: lin(this.o.accent) })); this.ring.visible = false; this.group.add(this.ring);

    const conc = makeConcreteTexture();
    this.plinth = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 72, 1), new THREE.MeshStandardMaterial({ color: lin(this.o.plinth), map: conc, bumpMap: conc, bumpScale: .012, roughness: 1 }));
    this.plinth.castShadow = true; this.plinth.receiveShadow = true; this.scene.add(this.plinth);
    this.floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.ShadowMaterial({ opacity: .2 }));
    this.floor.rotation.x = -Math.PI / 2; this.floor.receiveShadow = true; this.scene.add(this.floor);

    this.regenerate(true);
    this.loop = this.loop.bind(this);
    this.resize();
    if ('ResizeObserver' in window) new ResizeObserver(() => this.resize()).observe(canvas.parentElement);
    else addEventListener('resize', () => this.resize());
    watchVisible(canvas.parentElement, v => { this.visible = v; this.sync(); }, '0px');
    document.addEventListener('visibilitychange', () => this.sync());
  }
  regenerate(rebuild) {
    const g0 = this.mesh.geometry;
    if (rebuild || !g0 || g0.userData.sides !== this.p.sides) {
      if (g0) g0.dispose();
      const g = buildFormGeometry(this.p, this.o.resU, this.o.resV);
      this.mesh.geometry = g;
      const rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(g.userData.U * 3), 3));
      this.ring.geometry.dispose(); this.ring.geometry = rg;
    } else fillFormPositions(g0, this.p);
    if (this.view === 'layers') this.buildLayerLines();
    this.fit();
  }
  buildLayerLines() {
    const g = this.mesh.geometry, { U, V } = g.userData, src = g.attributes.position.array;
    const step = Math.max(1, Math.round(V / 60)), arr = new Float32Array((Math.floor(V / step) + 1) * U * 6);
    let k = 0;
    for (let j = 0; j <= V; j += step) for (let i = 0; i < U; i++) {
      const a = (j * U + i) * 3, b = (j * U + ((i + 1) % U)) * 3;
      arr[k++] = src[a]; arr[k++] = src[a + 1]; arr[k++] = src[a + 2]; arr[k++] = src[b]; arr[k++] = src[b + 1]; arr[k++] = src[b + 2];
    }
    this.layers.geometry.dispose();
    const lg = new THREE.BufferGeometry(); lg.setAttribute('position', new THREE.BufferAttribute(arr.subarray(0, k), 3)); this.layers.geometry = lg;
  }
  setColor(hex) { this.matSolid.color.copy(lin(hex)); this.renderOnce(); }
  setFinish(f) {
    const F = { mate: [.95, 0, .022], seda: [.38, .16, .012], piedra: [1, 0, .05] }[f] || [.95, 0, .022];
    this.matSolid.roughness = F[0]; this.matSolid.metalness = F[1]; this.matSolid.bumpScale = F[2]; this.renderOnce();
  }
  setView(v) {
    this.view = v;
    this.mesh.visible = v !== 'layers';
    this.mesh.material = v === 'wire' ? this.matWire : this.matSolid;
    this.mesh.castShadow = v === 'solid';
    this.layers.visible = v === 'layers';
    if (v === 'layers') this.buildLayerLines();
    this.renderOnce();
  }
  fit() {
    const pos = this.mesh.geometry.attributes.position.array;
    let m = 0; for (let i = 0; i < pos.length; i += 3) m = Math.max(m, pos[i] * pos[i] + pos[i + 2] * pos[i + 2]);
    const maxR = Math.sqrt(m), H = this.H = this.p.height / 10, ph = this.o.plinthH;
    const pr = maxR * 1.16 + .06;
    this.group.position.y = H / 2;
    this.plinth.scale.set(pr, ph, pr); this.plinth.position.y = -ph / 2;
    this.floor.position.y = -ph;
    const sc = this.key.shadow.camera, ext = Math.max(pr * 2.4, H * 1.2, 2.5);
    sc.left = -ext; sc.right = ext; sc.top = ext; sc.bottom = -ext; sc.near = .5; sc.far = 30; sc.updateProjectionMatrix();
    const total = H + ph;
    this.target.set(0, (H - ph) / 2 + total * .03, 0);
    const tan = Math.tan((this.camera.fov * Math.PI) / 360), aspect = this.camera.aspect || 1;
    const needV = (total / 2) * 1.24 / tan, needH = pr * 1.55 / (tan * aspect);
    this.targetDist = Math.max(needV, needH) + pr;
    if (!this.dist) this.dist = this.targetDist;
  }
  resize() {
    const el = this.canvas.parentElement, w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h; this.camera.updateProjectionMatrix();
    this.fit(); this.dist = this.targetDist; this.renderOnce();
  }
  startBuild(dur = 2400) {
    if (PW.reduced) { this.plane.constant = 999; this.ring.visible = false; this.renderOnce(); return; }
    this.build = { start: performance.now(), dur }; this.plane.constant = -.01; this.sync();
  }
  updateBuild(now) {
    if (!this.build) return;
    const p = clamp((now - this.build.start) / this.build.dur, 0, 1), e = easeInOut(p);
    const g = this.mesh.geometry, { U, V } = g.userData, src = g.attributes.position.array, j = Math.min(V, Math.floor(e * V));
    this.plane.constant = e * (this.H + .01);
    const ra = this.ring.geometry.attributes.position.array;
    for (let i = 0; i < U; i++) { const s = (j * U + i) * 3; ra[i * 3] = src[s] * 1.015; ra[i * 3 + 1] = src[s + 1]; ra[i * 3 + 2] = src[s + 2] * 1.015; }
    this.ring.geometry.attributes.position.needsUpdate = true;
    this.ring.visible = p < 1; this.buildProgress = p;
    if (p >= 1) { this.build = null; this.plane.constant = 999; }
  }
  sync() {
    const should = this.visible && !document.hidden;
    if (should && !this.running) { this.running = true; this.lastT = performance.now(); requestAnimationFrame(this.loop); }
    else if (!should) this.running = false;
  }
  renderOnce() {
    const c = this.camera, t = this.target;
    c.position.set(t.x, t.y + Math.sin(this.elev) * this.dist, Math.cos(this.elev) * this.dist);
    c.lookAt(t);
    this.group.rotation.y = this.rotY;
    this.renderer.render(this.scene, c);
  }
  loop(now) {
    if (!this.running) return;
    requestAnimationFrame(this.loop);
    const dt = Math.min(.05, (now - this.lastT) / 1000); this.lastT = now;
    if (this.onFrame) this.onFrame(dt, now);
    this.updateBuild(now);
    this.rotY += (PW.reduced ? 0 : this.o.autoRotate) * dt + this.rotVel * dt;
    this.rotVel *= Math.pow(.05, dt);
    this.elev = lerp(this.elev, this.targetElev, 1 - Math.pow(.002, dt));
    this.dist = lerp(this.dist, this.targetDist, 1 - Math.pow(.01, dt));
    this.renderOnce();
  }
}
function webglFallback(host) { const d = document.createElement('div'); d.className = 'pw-fallback'; d.textContent = 'La vista 3D no está disponible en este navegador.'; host.appendChild(d); }

/* ---------- 03. PRELOADER: secuencia de obra ---------- */
function initPreloader(done) {
  let seen = false; try { seen = sessionStorage.getItem('arko-intro') === '1'; sessionStorage.setItem('arko-intro', '1'); } catch (e) { /* sin almacenamiento */ }
  if (document.body.dataset.page !== 'inicio' || seen) return done();
  const el = document.createElement('div'); el.className = 'pw-preloader'; el.setAttribute('aria-hidden', 'true'); el.innerHTML = CHROME.preloader;
  document.body.append(el);
  const log = $('.pw-preloader__log', el), bar = $('.pw-preloader__bar span', el), pct = $('.pw-preloader__pct', el);
  const lines = ['Montando encofrado ......... <span>ok</span>', 'Vertiendo la forma ......... <span>ok</span>', 'Vibrado de la malla ........ <span>ok</span>', 'Fraguado ................... <span>ok</span>', 'Desencofrando'];
  const total = PW.reduced ? 250 : 1800, t0 = performance.now();
  let shown = 0, finished = false;
  const finish = () => {
    if (finished) return; finished = true;
    pct.textContent = '100%'; bar.style.width = '100%';
    setTimeout(() => { el.classList.add('is-done'); done(); setTimeout(() => el.remove(), 1200); }, PW.reduced ? 0 : 250);
  };
  const tick = now => {
    const p = clamp((now - t0) / total, 0, 1);
    while (shown < Math.min(lines.length, Math.floor(p * lines.length) + 1)) { const r = document.createElement('p'); r.innerHTML = lines[shown++]; log.appendChild(r); }
    const e = Math.floor(easeInOut(p) * 100); pct.textContent = e + '%'; bar.style.width = e + '%';
    if (p < 1) requestAnimationFrame(tick); else finish();
  };
  requestAnimationFrame(tick);
  setTimeout(finish, 4000);
}

/* ---------- 04. CURSOR (anillo que se vuelve marco en los botones) ---------- */
function initCursor() {
  if (!PW.fine) return;
  const cur = $('.pw-cursor'); if (!cur) return;
  document.documentElement.classList.add('pw-has-cursor');
  const ring = $('.pw-cursor__ring', cur), dot = $('.pw-cursor__dot', cur), label = $('.pw-cursor__label', cur);
  let x = -100, y = -100, rx = x, ry = y, rw = 34, rh = 34, magnet = null, hover = false, text = '';
  const baseRect = el => { const r = el.getBoundingClientRect(), m = new DOMMatrixReadOnly(getComputedStyle(el).transform === 'none' ? undefined : getComputedStyle(el).transform); return { left: r.left - m.m41, top: r.top - m.m42, width: r.width, height: r.height }; };
  addEventListener('pointermove', e => {
    x = e.clientX; y = e.clientY; cur.classList.remove('is-hidden');
    if (magnet && !PW.reduced) { const r = baseRect(magnet); magnet.style.transform = `translate(${(x - r.left - r.width / 2) * .18}px,${(y - r.top - r.height / 2) * .28}px)`; }
  }, { passive: true });
  document.addEventListener('pointerleave', () => cur.classList.add('is-hidden'));
  document.addEventListener('pointerover', e => {
    const m = e.target.closest('[data-magnetic]');
    if (m !== magnet) { if (magnet) magnet.style.transform = ''; magnet = m; }
    hover = !!e.target.closest('a,button,input,label,summary,[role="button"]');
    const dc = e.target.closest('[data-cursor]'); text = dc ? dc.dataset.cursor : '';
    cur.classList.toggle('is-magnet', !!magnet);
  });
  (function loop() {
    requestAnimationFrame(loop);
    const k = PW.reduced ? 1 : .18;
    let tw = hover ? 54 : 34, th = tw, tx = x, ty = y;
    if (magnet) { const r = magnet.getBoundingClientRect(); tw = r.width + 14; th = r.height + 14; tx = r.left + r.width / 2; ty = r.top + r.height / 2; }
    rx = lerp(rx, tx, k); ry = lerp(ry, ty, k); rw = lerp(rw, tw, .22); rh = lerp(rh, th, .22);
    ring.style.width = rw + 'px'; ring.style.height = rh + 'px';
    ring.style.transform = `translate(${rx - rw / 2}px,${ry - rh / 2}px)`;
    dot.style.transform = `translate(${x - 2.5}px,${y - 2.5}px)`;
    label.textContent = text; label.style.transform = `translate(${x + 22}px,${y + 18}px)`;
  })();
}

/* ---------- 05. HEADER ---------- */
function initHeader() {
  const header = $('.pw-header'), clock = $('#pw-clock'), gen = $('#pw-gen-count'), cart = $('#pw-cart-count');
  const now = new Date(); let count = 140 + Math.floor((now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds()) / 43);
  const render = flash => { gen.textContent = pad(count, 4); if (flash) { gen.classList.add('is-flash'); setTimeout(() => gen.classList.remove('is-flash'), 600); } };
  render();
  const tick = () => (clock.textContent = new Date().toLocaleTimeString('es-ES', { hour12: false, timeZone: 'Europe/Madrid' }));
  tick(); setInterval(tick, 1000);
  (function bump() { setTimeout(() => { count += 1 + Math.floor(Math.random() * 2); render(true); bump(); }, 3000 + Math.random() * 5000); })();
  on('generated', () => { count++; render(true); });
  on('cart:count', n => { cart.textContent = n; const b = $('.pw-header__cart'); b.classList.add('is-bump'); setTimeout(() => b.classList.remove('is-bump'), 700); });
  const menu = $('.pw-header__menu');
  const setOpen = o => { header.classList.toggle('is-open', o); menu.setAttribute('aria-expanded', o); menu.textContent = o ? 'Cerrar' : 'Menú'; };
  menu.addEventListener('click', () => setOpen(!header.classList.contains('is-open')));
  $$('.pw-header__nav a').forEach(a => a.addEventListener('click', () => setOpen(false)));
}

/* ---------- 06. REVEAL + FRAGUADO + LUZ RASANTE ---------- */
function initReveal() {
  const els = $$('.pw-reveal');
  if (PW.reduced || !('IntersectionObserver' in window)) { els.forEach(e => e.classList.add('is-in')); return; }
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } }), { threshold: .1, rootMargin: '0px 0px -8% 0px' });
  els.forEach(e => io.observe(e));
}
// Divide un titular en letras (conserva <br> y spans) para que "fragüen" al cargar
function splitLetters(el) {
  let i = 0;
  const walk = node => {
    Array.from(node.childNodes).forEach(ch => {
      if (ch.nodeType === 3) {
        // letras dentro de palabras que no se parten
        const frag = document.createDocumentFragment();
        ch.nodeValue.split(/(\s+)/).forEach(w => {
          if (!w) return;
          if (/^\s+$/.test(w)) { frag.appendChild(document.createTextNode(' ')); return; }
          const word = document.createElement('span'); word.className = 'pw-word'; word.setAttribute('aria-hidden', 'true');
          for (const c of w) { const s = document.createElement('span'); s.className = 'pw-ch'; s.style.setProperty('--i', i++); s.textContent = c; word.appendChild(s); }
          frag.appendChild(word);
        });
        ch.replaceWith(frag);
      } else if (ch.nodeType === 1 && ch.tagName !== 'BR') walk(ch);
    });
  };
  walk(el);
}
function initRakingLight() {
  if (!PW.fine || PW.reduced) return;
  $$('.pw-rake').forEach(el => {
    let raf = 0, ex = 0, ey = 0;
    el.addEventListener('pointermove', e => {
      ex = e.clientX; ey = e.clientY;
      if (raf) return;
      raf = requestAnimationFrame(() => { raf = 0; const r = el.getBoundingClientRect(); el.style.setProperty('--lx', (ex - r.left) + 'px'); el.style.setProperty('--ly', (ey - r.top) + 'px'); });
    });
  });
}

/* ---------- 07. HERO + FRANJA ---------- */
function initHero() {
  const canvas = $('.pw-hero__canvas'); if (!canvas) return;
  if (!PW.hasThree) return webglFallback(canvas.parentElement);
  const base = { type: 'vase', height: 26, twist: 70, sides: 7, wave: .12, seed: 48213 };
  const stage = new FormStage(canvas, { params: base, tone: 0xC4B39C, resU: PW.isMobile() ? 56 : 84, resV: PW.isMobile() ? 80 : 120, autoRotate: .14, elev: .12, key: [-3.6, 4.4, 2.6] });
  const twistOut = $('[data-hero-twist]'), diamOut = $('[data-hero-diam]');
  diamOut.textContent = Math.round(stage.plinth.scale.x / 1.16 * 20);
  let mx = 0, my = 0, frame = 0;
  if (PW.fine) addEventListener('pointermove', e => { mx = e.clientX / innerWidth * 2 - 1; my = e.clientY / innerHeight * 2 - 1; }, { passive: true });
  const cur = { twist: base.twist, wave: base.wave };
  stage.onFrame = (dt, now) => {
    if (PW.reduced) return;
    // El puntero modela la pieza con suavidad: X → torsión, Y → ondulación
    const auto = PW.fine ? 0 : Math.sin(now / 2600);
    const tT = base.twist + (mx + auto) * 90, tW = clamp(base.wave + (PW.fine ? (1 - (my + 1) / 2) : .5 + .5 * Math.sin(now / 3100)) * .35, 0, 1);
    const k = 1 - Math.pow(.05, dt), nt = lerp(cur.twist, tT, k), nw = lerp(cur.wave, tW, k);
    if (Math.abs(nt - cur.twist) > .05 || Math.abs(nw - cur.wave) > .0008) { cur.twist = nt; cur.wave = nw; stage.p.twist = nt; stage.p.wave = nw; fillFormPositions(stage.mesh.geometry, stage.p); }
    stage.targetElev = .12 + my * .06;
    if (++frame % 10 === 0) twistOut.textContent = Math.round(cur.twist);
  };
  stage.plane.constant = -99; stage.renderOnce();
  on('ready', () => stage.startBuild(3000));
}
function initStrip() {
  const strip = $('.pw-strip'); if (!strip) return;
  const track = $('.pw-strip__track', strip), unit = track.innerHTML;
  let guard = 0; while (track.scrollWidth < innerWidth * 2 && guard++ < 10) track.insertAdjacentHTML('beforeend', unit);
  track.insertAdjacentHTML('beforeend', track.innerHTML);
  let half = track.scrollWidth / 2;
  addEventListener('resize', () => (half = track.scrollWidth / 2));
  if (PW.reduced) return;
  let x = 0, vel = 0, lastY = scrollY, visible = false, running = false, last = 0;
  addEventListener('scroll', () => { vel += scrollY - lastY; lastY = scrollY; }, { passive: true });
  const loop = now => {
    if (!visible) { running = false; return; }
    requestAnimationFrame(loop);
    const dt = Math.min(.05, (now - last) / 1000); last = now;
    vel *= Math.pow(.03, dt);
    x -= (28 + Math.min(260, Math.abs(vel) * 2.2)) * (vel < -2 ? -1 : 1) * dt;
    if (x <= -half) x += half; if (x > 0) x -= half;
    track.style.transform = `translate3d(${x}px,0,0)`;
  };
  watchVisible(strip, v => { visible = v; if (v && !running) { running = true; last = performance.now(); requestAnimationFrame(loop); } });
}

/* ---------- 08. PROCESO ---------- */
function initProcess() {
  // 8.1 intención que se escribe sola
  (function () {
    const box = $('[data-viz="prompt"]'); if (!box) return;
    const out = $('[data-typer]', box), cnt = $('[data-typer-count]', box);
    const prompts = ['jarrón alto de torsión lenta, sección hexagonal, que recoja la luz de la tarde', 'lámpara que se abre como un arco, luz cálida y rasante', 'bandeja baja con curvas de nivel, gris basalto', 'maceta pesada, octogonal, escalonada como un zigurat'];
    if (PW.reduced) { out.textContent = prompts[0]; cnt.textContent = prompts[0].split(' ').length; return; }
    let pi = 0, ci = 0, dir = 1, visible = false, timer = null;
    const step = () => {
      if (!visible) { timer = null; return; }
      const s = prompts[pi]; ci += dir; out.textContent = s.slice(0, ci); cnt.textContent = s.slice(0, ci).split(' ').filter(Boolean).length;
      let d = dir > 0 ? 40 + Math.random() * 60 : 14;
      if (dir > 0 && ci >= s.length) { dir = -1; d = 2200; } else if (dir < 0 && ci <= 0) { dir = 1; pi = (pi + 1) % prompts.length; d = 500; }
      timer = setTimeout(step, d);
    };
    watchVisible(box, v => { visible = v; if (v && !timer) step(); });
  })();
  // 8.2 malla girando en la hornacina
  (function () {
    const box = $('[data-viz="wire"]'); if (!box) return;
    const cv = $('canvas', box), ctx = cv.getContext('2d'), read = $('[data-wire-read]', box);
    const p = { type: 'vase', height: 24, twist: 60, sides: 32, wave: .35, seed: 48213 }, c = PWForm.coeffs(p.seed), ROWS = 16, COLS = 18, tmp = [0, 0, 0];
    let w = 0, h = 0, rot = 0, visible = false, running = false, last = 0;
    const size = () => { const r = box.getBoundingClientRect(), dpr = Math.min(2, devicePixelRatio || 1); w = r.width; h = r.height; cv.width = w * dpr; cv.height = h * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0); };
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      const S = h / 4.1, cx = w / 2, by = h * .8, pts = [];
      for (let j = 0; j <= ROWS; j++) { const row = []; for (let i = 0; i < COLS; i++) { PWForm.point(p, c, j / ROWS, (i / COLS) * Math.PI * 2 + rot, tmp); row.push([cx + tmp[0] * S, by - tmp[1] * S + tmp[2] * S * .22, tmp[2]]); } pts.push(row); }
      ctx.lineWidth = 1;
      const seg = (a, b) => { ctx.strokeStyle = a[2] + b[2] > 0 ? 'rgba(58,50,42,.85)' : 'rgba(58,50,42,.16)'; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke(); };
      for (let j = 0; j <= ROWS; j++) for (let i = 0; i < COLS; i++) { seg(pts[j][i], pts[j][(i + 1) % COLS]); if (j < ROWS) seg(pts[j][i], pts[j + 1][i]); }
      read.textContent = `${fmt((ROWS + 1) * COLS)} vértices · ${pad(((rot * 57.3) % 360) | 0, 3)}°`;
    };
    const loop = now => { if (!visible) { running = false; return; } requestAnimationFrame(loop); rot += Math.min(.05, (now - last) / 1000) * .35; last = now; p.twist = 60 + Math.sin(now / 1800) * 40; draw(); };
    size(); draw(); addEventListener('resize', () => { size(); draw(); });
    if (PW.reduced) return;
    watchVisible(box, v => { visible = v; if (v && !running) { running = true; last = performance.now(); requestAnimationFrame(loop); } });
  })();
  // 8.3 capas que se apilan
  (function () {
    const box = $('[data-viz="layers"]'); if (!box) return;
    const stack = $('.pw-viz-layers__stack', box), read = $('[data-layers-read]', box), N = 20, c = PWForm.coeffs(771), rs = [];
    for (let i = 0; i < N; i++) rs.push(PWForm.radius('vase', i / (N - 1), c));
    const maxR = Math.max(...rs), els = rs.map(r => { const d = document.createElement('div'); d.className = 'pw-viz-layers__layer'; d.style.width = (r / maxR * 100) + '%'; stack.appendChild(d); return d; });
    if (PW.reduced) { els.forEach(e => e.classList.add('is-on')); read.textContent = 'Capa 120 / 120'; return; }
    let i = 0, visible = false, timer = null;
    const step = () => {
      if (!visible) { timer = null; return; }
      if (i < N) { els.forEach(e => e.classList.remove('is-current')); els[i].classList.add('is-on', 'is-current'); i++; read.textContent = `Capa ${pad(Math.round(i / N * 120), 3)} / 120`; timer = setTimeout(step, 220); }
      else timer = setTimeout(() => { els.forEach(e => e.classList.remove('is-on', 'is-current')); i = 0; timer = setTimeout(step, 600); }, 1800);
    };
    watchVisible(box, v => { visible = v; if (v && !timer) step(); });
  })();
  // 8.4 boquilla recorriendo la trayectoria
  (function () {
    const box = $('[data-viz="print"]'); if (!box) return;
    const guide = $('.pw-print__guide', box), path = $('.pw-print__path', box), head = $('.pw-print__head', box), gx = $('[data-g="x"]', box), gy = $('[data-g="y"]', box), read = $('[data-print-read]', box);
    const circ = (r, cx = 75, cy = 118) => Array.from({ length: 49 }, (_, i) => { const a = i / 48 * Math.PI * 2; return `${(cx + r * Math.cos(a)).toFixed(2)},${(cy + r * Math.sin(a) * .9).toFixed(2)}`; });
    let d = 'M' + circ(44).join(' L') + ' L' + circ(39).join(' L');
    for (let y = 88, k = 0; y <= 148; y += 6, k++) { const hw = Math.sqrt(Math.max(0, 34 * 34 - ((y - 118) / .9) ** 2)); d += k % 2 ? ` L${75 + hw},${y} L${75 - hw},${y}` : ` L${75 - hw},${y} L${75 + hw},${y}`; }
    guide.setAttribute('d', d); path.setAttribute('d', d);
    const L = path.getTotalLength(); path.style.strokeDasharray = L; path.style.strokeDashoffset = L;
    const place = s => {
      const pt = path.getPointAtLength(s);
      head.setAttribute('transform', `translate(${pt.x},${pt.y})`);
      gx.setAttribute('y1', pt.y); gx.setAttribute('y2', pt.y); gy.setAttribute('x1', pt.x); gy.setAttribute('x2', pt.x);
      path.style.strokeDashoffset = L - s;
      read.textContent = `X ${pt.x.toFixed(1).padStart(5, '0')} · Y ${pt.y.toFixed(1).padStart(5, '0')}`;
    };
    if (PW.reduced) { place(L); return; }
    let s = 0, hold = 0, visible = false, running = false, last = 0;
    const loop = now => { if (!visible) { running = false; return; } requestAnimationFrame(loop); const dt = Math.min(.05, (now - last) / 1000); last = now; if (hold > 0) { hold -= dt; if (hold <= 0) s = 0; return; } s += dt * 80; if (s >= L) { s = L; hold = 1.6; } place(s); };
    place(0);
    watchVisible(box, v => { visible = v; if (v && !running) { running = true; last = performance.now(); requestAnimationFrame(loop); } });
  })();
}

/* ---------- 09. TALLER ---------- */
function initLab() {
  const root = $('.pw-lab'); if (!root) return;
  const canvas = $('.pw-lab__canvas', root), form = $('.pw-lab__panel', root), json = $('[data-lab-json]', root), details = $('.pw-lab__json', root);
  const outs = {}; $$('[data-lab-out]', root).forEach(e => (outs[e.dataset.labOut] = e));
  if (PW.isMobile()) details.open = false;
  const p = { type: 'vase', height: 24, twist: 90, sides: 6, wave: .25, seed: 48213, colorId: 'cal', color: '#E4DCCD', colorName: 'Cal', finish: 'mate' };
  const incoming = store.get('arko-taller'); if (incoming) { Object.assign(p, incoming); store.del('arko-taller'); }
  let stage = null; const prev = {};
  // Muestras de color
  const sw = $('.pw-swatches', root), custom = $('.pw-custom', root), customInput = $('#pw-color');
  sw.innerHTML = COLORS.map(c => `<button type="button" class="pw-swatch" data-color="${c.id}" style="background:${c.hex}" aria-pressed="false" aria-label="${c.name}" title="${c.name}"></button>`).join('');
  $('[data-custom-fee]', root).textContent = `+${PRICING.customColor} €`;
  $('[data-delivery]', root).textContent = deliveryWindow();
  if (PW.hasThree) {
    stage = new FormStage(canvas, { params: p, tone: p.color, resU: PW.isMobile() ? 48 : 96, resV: PW.isMobile() ? 70 : 130, autoRotate: .2, elev: .16, key: [-2.6, 4.2, 3.6] });
    stage.plane.constant = -99;
    let drag = null;
    canvas.addEventListener('pointerdown', e => { drag = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener('pointermove', e => { if (!drag) return; const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag = { x: e.clientX, y: e.clientY }; stage.rotY += dx * .01; stage.rotVel = dx * .5; stage.targetElev = clamp(stage.targetElev + dy * .004, -.05, .9); });
    const end = () => (drag = null); canvas.addEventListener('pointerup', end); canvas.addEventListener('pointercancel', end);
    let built = false;
    watchVisible(canvas.parentElement, v => { if (v && !built) { built = true; stage.startBuild(2800); } }, '-15% 0px');
    stage.onFrame = () => { const pr = stage.build ? stage.buildProgress || 0 : 1; outs.progress.style.width = (pr * 100) + '%'; outs.status.textContent = pr < 1 ? `Imprimiendo ${Math.round(pr * 100)}%` : 'Lista'; };
  } else webglFallback(canvas.parentElement);

  const estimate = () => {
    let area = 0;
    if (stage) {
      const g = stage.mesh.geometry, P = g.attributes.position.array, I = g.index.array;
      for (let i = 0; i < I.length; i += 3) {
        const a = I[i] * 3, b = I[i + 1] * 3, c = I[i + 2] * 3;
        const ux = P[b] - P[a], uy = P[b + 1] - P[a + 1], uz = P[b + 2] - P[a + 2], vx = P[c] - P[a], vy = P[c + 1] - P[a + 1], vz = P[c + 2] - P[a + 2];
        const cx = uy * vz - uz * vy, cy = uz * vx - ux * vz, cz = ux * vy - uy * vx; area += Math.sqrt(cx * cx + cy * cy + cz * cz) / 2;
      }
    } else area = p.height / 10 * 3.4;
    const grams = area * 100 * .12 * 1.24, hours = grams / 11;
    return { grams, hours, price: priceOf(p), verts: stage ? stage.mesh.geometry.attributes.position.count : 0 };
  };
  const fmtTime = h => `${Math.floor(h)} h ${pad(Math.round((h % 1) * 60) % 60, 2)} min`;
  const renderJSON = est => {
    const data = { pieza: PWForm.code(p), tipo: p.type, altura_cm: p.height, torsion_grados: p.twist, lados: p.sides >= 32 ? 'redondo' : p.sides, ondulacion: +p.wave.toFixed(2), seed: p.seed, capa_mm: .2, capas: Math.round(p.height * 10 / .2), color: p.colorId === 'custom' ? `a medida ${p.color}` : p.colorName, acabado: FINISHES[p.finish].name, estimacion: { peso_g: +est.grams.toFixed(1), impresion: fmtTime(est.hours), precio_eur: est.price, plazo: '7 días + envío' } };
    const v = (k, val) => { const s = JSON.stringify(val), ch = prev[k] !== undefined && prev[k] !== s ? ' pw-json-changed' : ''; prev[k] = s; return `<span class="pw-json-v${ch}">${s}</span>`; };
    const keys = Object.keys(data), lines = ['{'];
    keys.forEach((k, i) => {
      const comma = i < keys.length - 1 ? ',' : '';
      if (typeof data[k] === 'object') { lines.push(`  <span class="pw-json-k">"${k}"</span>: {`); const sk = Object.keys(data[k]); sk.forEach((s, j) => lines.push(`    <span class="pw-json-k">"${s}"</span>: ${v(k + s, data[k][s])}${j < sk.length - 1 ? ',' : ''}`)); lines.push(`  }${comma}`); }
      else lines.push(`  <span class="pw-json-k">"${k}"</span>: ${v(k, data[k])}${comma}`);
    });
    lines.push('}'); json.innerHTML = lines.join('\n');
    clearTimeout(renderJSON.t); renderJSON.t = setTimeout(() => $$('.pw-json-changed', json).forEach(e => e.classList.remove('pw-json-changed')), 700);
    return data;
  };
  const outputs = { height: v => `${v} cm`, twist: v => `${v}°`, sides: v => (v >= 32 ? 'redondo' : v), wave: v => (+v).toFixed(2).replace('.', ','), seed: v => pad(v, 5) };
  const syncUI = () => {
    $$('input[type="range"]', form).forEach(inp => { inp.value = p[inp.name]; $(`[data-out="${inp.name}"]`, form).textContent = outputs[inp.name](p[inp.name]); });
    $$('[data-type]', form).forEach(b => b.setAttribute('aria-pressed', b.dataset.type === p.type));
    $$('[data-finish]', form).forEach(b => b.setAttribute('aria-pressed', b.dataset.finish === p.finish));
    $$('.pw-swatch', form).forEach(b => b.setAttribute('aria-pressed', b.dataset.color === p.colorId));
    custom.classList.toggle('is-active', p.colorId === 'custom');
    $('[data-out="colorName"]', form).textContent = p.colorId === 'custom' ? `A medida · ${p.color.toUpperCase()}` : p.colorName;
    if (stage) { stage.setColor(p.color); stage.setFinish(p.finish); }
  };
  const setColor = (id, hex) => {
    const c = COLORS.find(x => x.id === id);
    p.colorId = id; p.color = c ? c.hex : hex; p.colorName = c ? c.name : 'A medida';
    syncUI(); update(false, false);
  };
  sw.addEventListener('click', e => { const b = e.target.closest('[data-color]'); if (b) setColor(b.dataset.color); });
  customInput.addEventListener('input', () => setColor('custom', customInput.value));
  customInput.addEventListener('click', () => setColor('custom', customInput.value));
  $$('[data-finish]', form).forEach(b => b.addEventListener('click', () => { p.finish = b.dataset.finish; syncUI(); update(false, false); }));
  // Cargar una pieza de la colección en el taller
  on('lab:load', q => {
    Object.assign(p, q); syncUI(); update(true, true);
    $('.pw-lab__grid', root).scrollIntoView({ behavior: PW.reduced ? 'auto' : 'smooth' });
  });
  const update = (rebuild, animate) => {
    if (stage) { Object.assign(stage.p, p); stage.regenerate(rebuild); if (animate) stage.startBuild(1600); else stage.renderOnce(); }
    const est = estimate();
    outs.code.textContent = PWForm.code(p); outs.verts.textContent = fmt(est.verts);
    outs.weight.textContent = Math.round(est.grams) + ' g'; outs.time.textContent = fmtTime(est.hours); outs.price.textContent = `${est.price} €`;
    renderJSON(est);
  };
  let pending = false;
  form.addEventListener('input', e => {
    const t = e.target; if (t.type !== 'range') return; // el selector de color va aparte
    p[t.name] = t.name === 'wave' ? parseFloat(t.value) : parseInt(t.value, 10);
    $(`[data-out="${t.name}"]`, form).textContent = outputs[t.name](p[t.name]);
    if (!pending) { pending = true; requestAnimationFrame(() => { pending = false; update(false, false); }); }
  });
  $$('[data-type]', form).forEach(b => b.addEventListener('click', () => {
    p.type = b.dataset.type;
    if (p.type === 'tray' && p.height > 12) p.height = 6;
    if (p.type === 'candle' && p.height > 16) p.height = 10;
    if ((p.type === 'vase' || p.type === 'lamp') && p.height < 14) p.height = 24;
    syncUI(); update(true, true); emit('generated');
  }));
  $$('[data-view]', root).forEach(b => b.addEventListener('click', () => { $$('[data-view]', root).forEach(x => x.setAttribute('aria-pressed', x === b)); if (stage) stage.setView(b.dataset.view); }));
  $('[data-action="randomize"]', form).addEventListener('click', () => { p.seed = 1 + Math.floor(Math.random() * 99999); syncUI(); update(true, true); emit('generated'); });
  $('[data-action="mutate"]', form).addEventListener('click', () => {
    const types = ['vase', 'lamp', 'planter', 'tray', 'candle']; p.type = types[Math.floor(Math.random() * types.length)]; p.seed = 1 + Math.floor(Math.random() * 99999);
    p.height = p.type === 'tray' ? 4 + Math.floor(Math.random() * 6) : p.type === 'candle' ? 7 + Math.floor(Math.random() * 7) : 14 + Math.floor(Math.random() * 24);
    p.twist = Math.round((Math.random() * 2 - 1) * 240); p.sides = Math.random() < .3 ? 32 : 3 + Math.floor(Math.random() * 10); p.wave = +(Math.random() * .8).toFixed(2);
    syncUI(); update(true, true); emit('generated');
  });
  $('[data-action="order"]', form).addEventListener('click', () => {
    const q = Object.assign({}, p);
    emit('cart:add', {
      key: JSON.stringify(q), kind: 'custom', params: q, price: priceOf(q), color: q.color,
      name: `${TYPE_NAMES[q.type]} ${PWForm.code(q)}`,
      desc: `${q.height} cm · ${q.sides >= 32 ? 'redondo' : q.sides + ' lados'} · torsión ${q.twist}° · ${q.colorId === 'custom' ? 'color a medida ' + q.color.toUpperCase() : q.colorName} · ${FINISHES[q.finish].name}`,
    });
  });
  const copyBtn = $('[data-action="copy"]', root);
  const doCopy = e => {
    e.preventDefault(); e.stopPropagation();
    const txt = JSON.stringify(renderJSON(estimate()), null, 2);
    const ok = () => { copyBtn.textContent = 'Copiado'; setTimeout(() => (copyBtn.textContent = 'Copiar'), 1500); };
    const fallback = () => { const r = document.createRange(); r.selectNodeContents(json); const s = getSelection(); s.removeAllRanges(); s.addRange(r); };
    try { navigator.clipboard.writeText(txt).then(ok, fallback); } catch (err) { fallback(); }
  };
  copyBtn.addEventListener('click', doCopy);
  copyBtn.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') doCopy(e); });
  syncUI(); update(false, false);
}

/* ---------- 10. COLECCIÓN: render sombreado + sección constructiva ---------- */
const TONES = {
  arcilla: ['#6E4630', '#B37E5A', '#DDB596'],
  hormigon: ['#5E5852', '#A9A298', '#D4CEC4'],
  arena: ['#85765F', '#CDBEA5', '#EEE4D3'],
  carbon: ['#1E1C1A', '#4C4742', '#80786F'],
  hueso: ['#948876', '#DDD3C3', '#F7F1E7'],
};
let svgUid = 0;
function pieceSVG(p, mode) {
  const uid = 'pw' + (svgUid++), c = PWForm.coeffs(p.seed), H = p.height / 10, ROWS = 70, SAMPLES = 72, tmp = [0, 0, 0], rows = [];
  let maxX = 0;
  for (let j = 0; j <= ROWS; j++) {
    const t = j / ROWS; let mn = 0, mx = 0; const ring = [];
    for (let i = 0; i < SAMPLES; i++) { PWForm.point(p, c, t, (i / SAMPLES) * Math.PI * 2, tmp); ring.push([tmp[0], tmp[1], tmp[2]]); mn = Math.min(mn, tmp[0]); mx = Math.max(mx, tmp[0]); }
    rows.push({ y: t * H, mn, mx, ring }); maxX = Math.max(maxX, -mn, mx);
  }
  const sec = mode === 'section', tilt = sec ? 0 : .2;
  const W = maxX * 2, span = Math.max(H, W);
  const padX = span * (sec ? .55 : .45), padT = span * (sec ? .42 : .55), padB = span * (sec ? .3 : .22);
  const vbW = W + padX * 2, vbH = H + maxX * tilt * 2 + padT + padB;
  const X = x => (x + maxX + padX).toFixed(3), Y = (y, z = 0) => (padT + maxX * tilt + H - y + z * tilt).toFixed(3);
  const sw = (vbW / 420).toFixed(4), fs = (vbW / 34).toFixed(3);
  let s = `<svg viewBox="0 0 ${vbW.toFixed(3)} ${vbH.toFixed(3)}" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">`;
  const outline = () => { let d = `M${X(rows[0].mn)},${Y(0)}`; rows.forEach(r => (d += ` L${X(r.mn)},${Y(r.y)}`)); for (let j = ROWS; j >= 0; j--) d += ` L${X(rows[j].mx)},${Y(rows[j].y)}`; return d + 'Z'; };
  if (!sec) {
    const [dk, md, lt] = TONES[p.tone] || TONES.hueso;
    s += `<defs><linearGradient id="${uid}g" x1="0" x2="1" y1="0" y2="0"><stop offset="0" stop-color="${dk}"/><stop offset=".2" stop-color="${md}"/><stop offset=".4" stop-color="${lt}"/><stop offset=".66" stop-color="${md}"/><stop offset="1" stop-color="${dk}"/></linearGradient>`;
    s += `<filter id="${uid}b" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="${(maxX * .09).toFixed(3)}"/></filter></defs>`;
    // sombra arrojada hacia la derecha (luz desde la izquierda)
    s += `<ellipse cx="${X(maxX * .35)}" cy="${Y(0)}" rx="${(maxX * 1.35).toFixed(3)}" ry="${(maxX * .22).toFixed(3)}" fill="rgba(40,30,20,.34)" filter="url(#${uid}b)"/>`;
    s += `<path d="${outline()}" fill="url(#${uid}g)"/>`;
    if (p.sides < 32) for (let e = 0; e < p.sides; e++) {
      let seg = '', on = false; const phi = (e / p.sides) * Math.PI * 2;
      for (let j = 0; j <= ROWS; j++) { PWForm.point(p, c, j / ROWS, phi, tmp); if (tmp[2] > 0) { seg += `${on ? 'L' : 'M'}${X(tmp[0])},${Y(tmp[1])}`; on = true; } else on = false; }
      if (seg) s += `<path d="${seg}" fill="none" stroke="rgba(255,250,240,.2)" stroke-width="${sw}"/>`;
    }
    let lay = ''; for (let j = 1; j < ROWS; j++) lay += `M${X(rows[j].mn)},${Y(rows[j].y)}L${X(rows[j].mx)},${Y(rows[j].y)}`;
    s += `<path d="${lay}" stroke="rgba(30,22,16,.1)" stroke-width="${(sw * .8).toFixed(4)}"/>`;
    let mouth = ''; rows[ROWS].ring.forEach((q, i) => (mouth += `${i ? 'L' : 'M'}${X(q[0])},${Y(q[1], q[2])}`));
    s += `<path d="${mouth}Z" fill="${dk}" stroke="${lt}" stroke-width="${sw}" stroke-opacity=".6"/>`;
  } else {
    // Sección A–A: alzado a la izquierda, corte rayado a la derecha, cotas y eje
    const ink = '#2A2927', wall = maxX * .07, baseT = wall * 1.2;
    s += `<defs><pattern id="${uid}h" width="${(maxX * .09).toFixed(3)}" height="${(maxX * .09).toFixed(3)}" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="${(maxX * .09).toFixed(3)}" stroke="${ink}" stroke-width="${(sw * .9).toFixed(4)}"/></pattern></defs>`;
    let left = `M${X(0)},${Y(0)}`; rows.forEach(r => (left += ` L${X(r.mn)},${Y(r.y)}`)); left += ` L${X(0)},${Y(H)}`;
    s += `<path d="${left}" fill="none" stroke="${ink}" stroke-width="${(sw * 1.4).toFixed(4)}"/>`;
    let lay = ''; for (let j = 4; j < ROWS; j += 4) lay += `M${X(rows[j].mn)},${Y(rows[j].y)}L${X(0)},${Y(rows[j].y)}`;
    s += `<path d="${lay}" stroke="${ink}" stroke-opacity=".18" stroke-width="${sw}"/>`;
    let cut = `M${X(0)},${Y(0)}`; rows.forEach(r => (cut += ` L${X(r.mx)},${Y(r.y)}`));
    for (let j = ROWS; j >= 0; j--) { const yy = Math.max(rows[j].y, baseT); cut += ` L${X(Math.max(0, rows[j].mx - wall))},${Y(yy)}`; }
    cut += ` L${X(0)},${Y(baseT)}Z`;
    s += `<path d="${cut}" fill="url(#${uid}h)" stroke="${ink}" stroke-width="${(sw * 1.4).toFixed(4)}"/>`;
    const ext = span * .08;
    s += `<line x1="${X(0)}" y1="${Y(H + ext)}" x2="${X(0)}" y2="${Y(-ext)}" stroke="#9C5F38" stroke-width="${sw}" stroke-dasharray="${(maxX * .12).toFixed(3)} ${(maxX * .04).toFixed(3)} ${(maxX * .02).toFixed(3)} ${(maxX * .04).toFixed(3)}"/>`;
    const dx = -maxX - padX * .45, tk = maxX * .06;
    s += `<g stroke="${ink}" stroke-width="${sw}"><line x1="${X(dx)}" y1="${Y(0)}" x2="${X(dx)}" y2="${Y(H)}"/><line x1="${X(dx - tk)}" y1="${Y(-tk)}" x2="${X(dx + tk)}" y2="${Y(tk)}"/><line x1="${X(dx - tk)}" y1="${Y(H - tk)}" x2="${X(dx + tk)}" y2="${Y(H + tk)}"/></g>`;
    s += `<text transform="translate(${(+X(dx) - maxX * .1).toFixed(3)} ${Y(H / 2)}) rotate(-90)" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="${fs}" fill="${ink}">${p.height} cm</text>`;
    const rt = rows[ROWS].mx, dy = H + span * .16;
    s += `<g stroke="${ink}" stroke-width="${sw}"><line x1="${X(-rt)}" y1="${Y(dy)}" x2="${X(rt)}" y2="${Y(dy)}"/><line x1="${X(-rt - tk)}" y1="${Y(dy - tk)}" x2="${X(-rt + tk)}" y2="${Y(dy + tk)}"/><line x1="${X(rt - tk)}" y1="${Y(dy - tk)}" x2="${X(rt + tk)}" y2="${Y(dy + tk)}"/></g>`;
    s += `<text x="${X(0)}" y="${(+Y(dy) - maxX * .08).toFixed(3)}" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="${fs}" fill="${ink}">Ø ${Math.round(rt * 20)} cm</text>`;
    s += `<text x="${X(0)}" y="${(vbH - padB * .35).toFixed(3)}" text-anchor="middle" font-family="JetBrains Mono,monospace" font-size="${fs}" letter-spacing="${(vbW / 200).toFixed(3)}" fill="#5B5249">SECCIÓN A–A · E 1:4</text>`;
    s += `<line x1="${X(-maxX * 1.3)}" y1="${Y(0)}" x2="${X(maxX * 1.3)}" y2="${Y(0)}" stroke="${ink}" stroke-width="${(sw * 1.6).toFixed(4)}"/>`;
  }
  return s + '</svg>';
}
const AR = { 3: '3/4.6', 4: '3/4.4', 5: '3/4', 6: '4/3.6' };
function cardHTML(item, span) {
  return `<article class="pw-piece" style="--span:${span};--ar:${AR[span]}" data-id="${item.id}">
    <a class="pw-piece__niche pw-plaster" href="pieza.html#${item.id}" data-cursor="Ver" aria-label="${item.name}">
      <div class="pw-piece__render">${pieceSVG(Object.assign({ tone: item.tone }, item.form), 'render')}</div><div class="pw-piece__section"></div>
      <span class="pw-piece__tag">${item.tag}</span>
    </a>
    <div class="pw-piece__row"><span class="pw-piece__code">${item.code}</span><span class="pw-piece__price">${item.price} €</span></div>
    <h3 class="pw-piece__name"><a href="pieza.html#${item.id}">${item.name}</a></h3>
    <dl class="pw-piece__spec"><dt>Capa</dt><dd>${item.layer}</dd><dt>Impresión</dt><dd>${item.time}</dd><dt>Material</dt><dd>${item.material}</dd><dt>Alto</dt><dd>${item.form.height} cm</dd></dl>
    <p class="pw-piece__lead">Preparación 7 días + envío</p>
    <div class="pw-piece__actions"><button class="pw-btn pw-btn--sm" type="button" data-add data-magnetic>Añadir</button><button class="pw-btn pw-btn--sm pw-btn--line" type="button" data-customize data-magnetic>Personalizar</button></div>
  </article>`;
}
// Rejilla de tarjetas con acciones delegadas (colección, destacadas, relacionadas)
function renderCards(grid, items, spans) {
  const pattern = spans || (items.length <= 2 ? [6, 6] : [5, 4, 3, 3, 4, 5, 6, 6]);
  grid.innerHTML = items.map((it, i) => cardHTML(it, pattern[i % pattern.length])).join('');
  const cards = $$('.pw-piece', grid);
  cards.forEach((c, i) => { c.classList.add('pw-enter'); c.style.setProperty('--d', i * 70 + 'ms'); });
  requestAnimationFrame(() => requestAnimationFrame(() => cards.forEach(c => c.classList.add('is-in'))));
  if (grid._pwBound) return;
  grid._pwBound = true;
  const itemOf = el => CATALOG.find(x => x.id === el.closest('.pw-piece').dataset.id);
  grid.addEventListener('click', e => {
    if (e.target.closest('[data-add]')) addCatalogItem(itemOf(e.target));
    else if (e.target.closest('[data-customize]')) openInTaller(catalogParams(itemOf(e.target)));
  });
  const makeSection = e => {
    const card = e.target.closest && e.target.closest('.pw-piece'); if (!card) return;
    const sec = $('.pw-piece__section', card);
    if (!sec.firstChild) { const it = itemOf(card); sec.innerHTML = pieceSVG(Object.assign({ tone: it.tone }, it.form), 'section'); }
  };
  grid.addEventListener('pointerover', makeSection); grid.addEventListener('focusin', makeSection);
}
// Página Colección: filtros por familia (#jarrones, #lamparas…)
function initCollection() {
  const grid = $('[data-collection]'); if (!grid) return;
  const bar = $('[data-filters]');
  const slug = { vase: 'jarrones', lamp: 'lamparas', planter: 'macetas', tray: 'bandejas', candle: 'portavelas' };
  const types = Object.keys(FAMILIES).filter(t => CATALOG.some(i => i.form.type === t));
  bar.innerHTML = `<button type="button" data-f="todo">Todo <sup>${CATALOG.length}</sup></button>` +
    types.map(t => `<button type="button" data-f="${t}">${FAMILIES[t]} <sup>${CATALOG.filter(i => i.form.type === t).length}</sup></button>`).join('');
  const count = $('[data-collection-count]');
  const apply = f => {
    const items = f === 'todo' ? CATALOG : CATALOG.filter(i => i.form.type === f);
    $$('[data-f]', bar).forEach(b => b.setAttribute('aria-pressed', b.dataset.f === f));
    renderCards(grid, items);
    if (count) count.textContent = `${items.length} ${items.length === 1 ? 'pieza' : 'piezas'}`;
  };
  bar.addEventListener('click', e => {
    const b = e.target.closest('[data-f]'); if (!b) return;
    apply(b.dataset.f);
    try { history.replaceState(null, '', b.dataset.f === 'todo' ? location.pathname : '#' + slug[b.dataset.f]); } catch (err) { /* sin historial */ }
  });
  const fromHash = () => { const h = location.hash.slice(1), t = Object.keys(slug).find(k => slug[k] === h); apply(t || 'todo'); };
  addEventListener('hashchange', fromHash);
  fromHash();
}
// Portada: piezas destacadas
function initFeatured() {
  const grid = $('[data-featured]'); if (!grid) return;
  renderCards(grid, ['v042', 'l017', 'm031'].map(id => CATALOG.find(i => i.id === id)), [4, 4, 4]);
}
// Portada: visuales de las cuatro puertas
function initDoors() {
  const col = $('[data-door="coleccion"]'); if (!col) return;
  const it = CATALOG.find(i => i.id === 'v077');
  col.innerHTML = pieceSVG(Object.assign({ tone: 'arcilla' }, it.form, { twist: -160 }), 'render');
  const dots = $('[data-door="taller"]');
  if (dots) dots.innerHTML = `<span class="pw-door__dots">${COLORS.map(c => `<i style="background:${c.hex}"></i>`).join('')}</span>`;
}
// Página de pieza: pieza.html#v042
function initPieza() {
  const root = $('[data-pieza]'); if (!root) return;
  const canvas = $('.pw-product__canvas', root), out = {};
  $$('[data-p]').forEach(e => (out[e.dataset.p] = e)); // la sección constructiva está fuera de root
  let stage = null, item = null;
  const show = () => {
    item = CATALOG.find(i => i.id === location.hash.slice(1)) || CATALOG[0];
    const tone = TONES[item.tone][1];
    document.title = `${item.name} · ARKO`;
    out.family.textContent = `Colección · ${FAMILIES[item.form.type]}`;
    out.family.href = 'coleccion.html#' + { vase: 'jarrones', lamp: 'lamparas', planter: 'macetas', tray: 'bandejas', candle: 'portavelas' }[item.form.type];
    out.name.textContent = item.name; out.code.textContent = item.code; out.price.textContent = item.price + ' €';
    out.desc.textContent = item.desc; out.tag.textContent = item.tag;
    out.spec.innerHTML = [['Alto', item.form.height + ' cm'], ['Lados', item.form.sides >= 32 ? 'Redondo' : item.form.sides], ['Torsión', item.form.twist + '°'], ['Capa', item.layer], ['Impresión', item.time], ['Material', item.material], ['Color', TONE_NAMES[item.tone]], ['Seed', pad(item.form.seed, 5)]]
      .map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
    out.swatch.style.background = tone;
    out.delivery.textContent = deliveryWindow();
    out.section.innerHTML = pieceSVG(Object.assign({ tone: item.tone }, item.form), 'section');
    renderCards($('[data-related]'), CATALOG.filter(i => i.id !== item.id && i.form.type === item.form.type).concat(CATALOG.filter(i => i.id !== item.id && i.form.type !== item.form.type)).slice(0, 3), [4, 4, 4]);
    if (stage) { Object.assign(stage.p, item.form); stage.regenerate(true); stage.setColor(tone); stage.startBuild(1800); }
  };
  show();
  if (PW.hasThree && canvas) {
    try {
      stage = new FormStage(canvas, { params: Object.assign({}, item.form), tone: TONES[item.tone][1], resU: PW.isMobile() ? 56 : 96, resV: PW.isMobile() ? 80 : 130, autoRotate: .18, elev: .14, key: [-3.4, 4.6, 2.8] });
      stage.plane.constant = -99; stage.renderOnce();
      on('ready', () => stage.startBuild(2600));
      let drag = null;
      canvas.addEventListener('pointerdown', e => { drag = e.clientX; canvas.setPointerCapture(e.pointerId); });
      canvas.addEventListener('pointermove', e => { if (drag === null) return; stage.rotY += (e.clientX - drag) * .01; stage.rotVel = (e.clientX - drag) * .5; drag = e.clientX; });
      const end = () => (drag = null); canvas.addEventListener('pointerup', end); canvas.addEventListener('pointercancel', end);
    } catch (e) { webglFallback(canvas.parentElement); }
  } else if (canvas) webglFallback(canvas.parentElement);
  addEventListener('hashchange', () => { show(); scrollTo({ top: 0, behavior: PW.reduced ? 'auto' : 'smooth' }); });
  $('[data-p-add]', root).addEventListener('click', () => addCatalogItem(item));
  $('[data-p-custom]', root).addEventListener('click', () => openInTaller(catalogParams(item)));
  const link = $('[data-p-custom-link]', root); if (link) link.addEventListener('click', e => { e.preventDefault(); openInTaller(catalogParams(item)); });
}

/* ---------- 10b. CESTA ----------
   Guarda la cesta en el navegador del cliente. "Pagar" envía los artículos a
   CHECKOUT_ENDPOINT (función de servidor que crea el pago en Stripe).
   Sin servidor, la página funciona en modo demostración. */
const CHECKOUT_ENDPOINT = '/api/checkout';
function initCart() {
  const panel = $('#pw-cart'), veil = $('.pw-cart-veil'), list = $('.pw-cart__list', panel), empty = $('.pw-cart__empty', panel);
  const out = {}; $$('[data-cart]', panel).forEach(e => (out[e.dataset.cart] = e));
  const pay = $('[data-cart-pay]', panel), msg = $('.pw-cart__msg', panel);
  let items = [];
  try { items = JSON.parse(localStorage.getItem('arko-cesta') || '[]'); } catch (e) { items = []; }
  const save = () => { try { localStorage.setItem('arko-cesta', JSON.stringify(items)); } catch (e) { /* sin almacenamiento */ } };
  const count = () => items.reduce((n, i) => n + i.qty, 0);
  const render = () => {
    list.innerHTML = items.map((it, i) => `
      <li class="pw-cart__item">
        <span class="pw-cart__thumb"><i style="background:${it.color}"></i></span>
        <div>
          <p class="pw-cart__name">${it.name}</p>
          <p class="pw-cart__desc">${it.desc}</p>
          <span class="pw-cart__qty"><button type="button" data-q="-1" data-i="${i}" aria-label="Quitar una">−</button><span>${it.qty}</span><button type="button" data-q="1" data-i="${i}" aria-label="Añadir una">+</button></span>
          <button type="button" class="pw-cart__remove" data-del="${i}">Eliminar</button>
        </div>
        <span class="pw-cart__price">${money(it.price * it.qty)}</span>
      </li>`).join('');
    const sub = items.reduce((n, i) => n + i.price * i.qty, 0), ship = shippingOf(sub);
    empty.hidden = items.length > 0;
    out.subtotal.textContent = money(sub);
    out.shipping.textContent = sub === 0 ? '—' : ship === 0 ? 'Gratis' : money(ship);
    out.total.textContent = money(Math.round((sub + ship) * 100) / 100);
    out.eta.textContent = items.length ? deliveryWindow() : `Envío gratis a partir de ${PRICING.freeShippingFrom} €.`;
    pay.disabled = !items.length;
    $('#pw-cart-count').textContent = count();
  };
  let lastFocus = null;
  const open = () => {
    lastFocus = document.activeElement;
    veil.hidden = false; requestAnimationFrame(() => { veil.classList.add('is-open'); panel.classList.add('is-open'); });
    panel.setAttribute('aria-hidden', 'false'); msg.textContent = '';
    setTimeout(() => $('.pw-cart__close', panel).focus(), 50);
  };
  const close = () => {
    veil.classList.remove('is-open'); panel.classList.remove('is-open'); panel.setAttribute('aria-hidden', 'true');
    setTimeout(() => (veil.hidden = true), 400);
    if (lastFocus) lastFocus.focus();
  };
  on('cart:add', it => {
    const found = items.find(x => x.key === it.key);
    if (found) found.qty++; else items.push(Object.assign({ qty: 1 }, it));
    save(); render(); emit('cart:count', count()); open();
  });
  list.addEventListener('click', e => {
    const q = e.target.closest('[data-q]'), d = e.target.closest('[data-del]');
    if (q) { const it = items[+q.dataset.i]; it.qty = Math.max(0, it.qty + +q.dataset.q); if (!it.qty) items.splice(+q.dataset.i, 1); }
    else if (d) items.splice(+d.dataset.del, 1);
    else return;
    save(); render();
  });
  $$('[data-cart-close]').forEach(b => b.addEventListener('click', close));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && panel.classList.contains('is-open')) close(); });
  $('.pw-header__cart').addEventListener('click', open);
  pay.addEventListener('click', async () => {
    msg.textContent = 'Preparando el pago seguro…';
    try {
      const res = await fetch(CHECKOUT_ENDPOINT, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: items.map(i => ({ kind: i.kind, code: i.code, params: i.params, qty: i.qty })) }),
      });
      if (!res.ok) throw new Error(res.status);
      const { url } = await res.json();
      if (!url) throw new Error('sin url');
      location.href = url;
    } catch (e) {
      msg.textContent = 'Modo demostración: el pago con tarjeta se activa al publicar la web con su función de pago (Stripe). Tu cesta se ha guardado.';
    }
  });
  render();
  // Vuelta desde Stripe tras pagar
  if (new URLSearchParams(location.search).get('pedido') === 'ok') {
    items = []; save(); render(); open();
    msg.textContent = 'Pedido recibido. Te enviaremos la confirmación por correo y empezamos a imprimir: en 7 días sale hacia tu casa.';
  }
}

/* ---------- 11. MANIFIESTO ---------- */
function initManifesto() {
  const sec = $('.pw-manifesto'), text = $('[data-manifesto]'); if (!sec || !text) return;
  text.innerHTML = text.textContent.trim().split(/\s+/).map(w => { const a = w.startsWith('*'); return `<span class="pw-manifesto__w${a ? ' is-accent' : ''}">${a ? w.slice(1) : w}</span>`; }).join(' ');
  const words = $$('.pw-manifesto__w', text), bar = $('.pw-manifesto__bar i', sec), pct = $('[data-manifesto-pct]', sec);
  if (PW.reduced) { words.forEach(w => w.classList.add('is-on')); bar.style.width = '100%'; pct.textContent = '100%'; return; }
  let ticking = false, lastN = -1, active = false;
  const update = () => {
    ticking = false;
    const r = sec.getBoundingClientRect(), prog = clamp((-r.top + innerHeight * .3) / Math.max(1, r.height - innerHeight), 0, 1), n = Math.round(prog * words.length);
    if (n !== lastN) { words.forEach((w, i) => w.classList.toggle('is-on', i < n)); lastN = n; }
    bar.style.width = (prog * 100) + '%'; pct.textContent = pad(Math.round(prog * 100), 3) + '%';
  };
  const onScroll = () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } };
  watchVisible(sec, v => { if (v && !active) { active = true; addEventListener('scroll', onScroll, { passive: true }); update(); } else if (!v && active) { active = false; removeEventListener('scroll', onScroll); } });
}

/* ---------- 12. CIFRAS ---------- */
function initStats() {
  const run = el => {
    const target = parseFloat(el.dataset.count), dec = parseInt(el.dataset.decimals || '0', 10);
    if (PW.reduced) { el.textContent = fmt(target, dec); return; }
    const t0 = performance.now(), dur = 2600;
    const tick = now => { const p = clamp((now - t0) / dur, 0, 1); el.textContent = fmt(target * easeOutExpo(p), dec); if (p < 1) requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
  };
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return; io.unobserve(e.target); run(e.target);
    const m = $('[data-meter]', e.target.closest('.pw-stat')); if (m) m.style.width = (parseFloat(m.dataset.meter) * 100) + '%';
  }), { threshold: .4 });
  $$('[data-count]').forEach(n => io.observe(n));
}

/* ---------- 13. NEWSLETTER ---------- */
function initNewsletter() {
  const form = $('.pw-news__form'); if (!form) return;
  const input = $('.pw-news__input', form), block = $('.pw-news__block', form), mirror = $('.pw-news__mirror', form), wrap = $('.pw-news__wrap', form), log = $('.pw-news__log');
  const caret = () => { mirror.textContent = input.value.slice(0, input.selectionStart ?? input.value.length); block.style.left = Math.max(0, Math.min(mirror.offsetWidth - input.scrollLeft, wrap.clientWidth - block.offsetWidth)) + 'px'; };
  ['input', 'keyup', 'click', 'focus', 'blur', 'select'].forEach(ev => input.addEventListener(ev, caret)); caret();
  const print = (t, cls) => { const p = document.createElement('p'); p.textContent = t; if (cls) p.className = cls; log.appendChild(p); while (log.children.length > 4) log.firstChild.remove(); };
  form.addEventListener('submit', e => {
    e.preventDefault(); const v = input.value.trim();
    print(`$ suscribir ${v || '""'}`);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) { print('Ese correo no parece válido. Revísalo y vuelve a enviarlo.', 'is-err'); input.focus(); return; }
    setTimeout(() => { print('Suscripción registrada. El próximo cuaderno sale el día 1.', 'is-ok'); input.value = ''; caret(); }, PW.reduced ? 0 : 600);
  });
}

/* ---------- 14. FOOTER: nombre a todo el ancho ---------- */
function initFooter() {
  const brand = $('.pw-footer__brand'); if (!brand) return;
  $$('[data-year]').forEach(e => (e.textContent = new Date().getFullYear()));
  const fit = () => { brand.style.fontSize = '100px'; const w = brand.getBoundingClientRect().width; if (w) brand.style.fontSize = (100 * brand.parentElement.clientWidth / w * .99) + 'px'; };
  fit(); addEventListener('resize', fit); if (document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
}

/* ---------- 15. ARRANQUE ---------- */
function boot() {
  const page = document.body.dataset.page || 'inicio';
  document.body.dataset.page = page;
  injectChrome(page);
  try { makeWallTextures(); } catch (e) { /* se quedan las texturas SVG */ }
  const titles = $$('.pw-set'); titles.forEach(splitLetters);
  initCursor(); initHeader(); initCart(); initReveal(); initRakingLight(); initStrip(); initProcess();
  initCollection(); initFeatured(); initDoors(); initManifesto(); initStats(); initNewsletter(); initFooter();
  try { initHero(); } catch (e) { console.warn('[arko] hero', e); webglFallback($('.pw-arch')); }
  try { initLab(); } catch (e) { console.warn('[arko] taller', e); }
  try { initPieza(); } catch (e) { console.warn('[arko] pieza', e); }
  initPreloader(() => { titles.forEach(t => t.classList.add('is-set')); emit('ready'); });
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
