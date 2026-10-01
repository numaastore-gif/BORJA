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

/* ---------- 00b. TIENDA ----------
   Precios, líneas de filamento, colores oficiales Bambu Lab y modelos fijos
   vienen de assets/arko-data.js (generado por tools/arko_data.py), el mismo
   origen que usa api/checkout.js para recalcular el precio en el servidor. */
const DATA = window.ARKO_DATA || { lines: {}, pricing: { base: {}, perCm: {} }, catalog: [], filaments: [] };
const LINES = DATA.lines, PRICING = DATA.pricing, CATALOG = DATA.catalog, FILAMENTS = DATA.filaments;
const FIL = Object.fromEntries(FILAMENTS.map(f => [f.code, f]));
const TYPE_NAMES = { vase: 'Jarrón', lamp: 'Lámpara', planter: 'Maceta', tray: 'Bandeja', candle: 'Portavelas' };
const SHAPES = { organica: 'Orgánica', columna: 'Columna', caliz: 'Cáliz', bulbo: 'Bulbo', cono: 'Cono', reloj: 'Reloj' };
const TEXTURES = { lisa: 'Lisa', ondas: 'Ondas', estrias: 'Estrías', costillas: 'Costillas', relieve: 'Relieve' };
const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const cleanEngrave = s => String(s || '').replace(/[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9 .,&'·-]/g, '').slice(0, 14);
// Rellena los campos que falten (configuraciones antiguas o incompletas)
function normalizeParams(q) {
  const p = Object.assign(JSON.parse(JSON.stringify(CATALOG[0] ? CATALOG[0].params : {})), q || {});
  if (!TYPE_NAMES[p.type]) p.type = 'vase';
  if (!SHAPES[p.shape]) p.shape = 'organica';
  if (!TEXTURES[p.tex]) p.tex = 'lisa';
  if (!LINES[p.line]) p.line = 'matte';
  if (!FIL[p.color] || FIL[p.color].line !== p.line) p.color = FILAMENTS.find(f => f.line === p.line).code;
  if (p.line === 'gradient') p.mode = 'solid';
  if (p.mode === 'bicolor' && (!FIL[p.color2] || FIL[p.color2].line !== p.line || p.color2 === p.color)) p.color2 = FILAMENTS.find(f => f.line === p.line && f.code !== p.color).code;
  if (p.mode !== 'bicolor') { p.mode = 'solid'; }
  p.engrave = cleanEngrave(p.engrave);
  if (!(p.type === 'vase' || p.type === 'planter')) p.watertight = false;
  return p;
}
function priceOf(p) {
  let pr = (PRICING.base[p.type] ?? 29) + (PRICING.perCm[p.type] ?? 1.2) * p.height * (p.width ?? 1) + (LINES[p.line] ? LINES[p.line].fee : 0);
  if (p.mode === 'bicolor') pr += PRICING.bicolor;
  if (p.watertight) pr += PRICING.watertight;
  if (p.engrave) pr += PRICING.engrave;
  return Math.round(pr);
}
const shippingOf = subtotal => (subtotal === 0 ? 0 : subtotal >= PRICING.freeShippingFrom ? 0 : PRICING.shipping);
const money = n => (Number.isInteger(n) ? n : n.toFixed(2).replace('.', ',')) + ' €';
function deliveryWindow(from = new Date()) {
  const start = new Date(from); start.setDate(start.getDate() + PRICING.prepDays);
  const add = (d, n) => { const x = new Date(d); while (n > 0) { x.setDate(x.getDate() + 1); if (x.getDay() !== 0 && x.getDay() !== 6) n--; } return x; };
  const f = d => d.toLocaleDateString('es-ES', { weekday: 'short', day: 'numeric', month: 'short' }).replace(',', '');
  return `Si lo pides hoy, llega entre el ${f(add(start, PRICING.shipMin))} y el ${f(add(start, PRICING.shipMax))}.`;
}
// Color de muestra exactamente como lo publica Bambu Lab (degradado: de abajo arriba)
const swatchCSS = code => { const f = FIL[code]; if (!f) return '#ccc'; return f.hex.length > 1 ? `linear-gradient(0deg, ${f.hex[0]}, ${f.hex[1]})` : f.hex[0]; };
const filLabel = code => { const f = FIL[code]; return f ? `${LINES[f.line].name} · ${f.name} · ${f.code}` : ''; };
function describe(p) {
  const parts = [TYPE_NAMES[p.type] + (p.type === 'vase' ? ' ' + SHAPES[p.shape].toLowerCase() : ''), `${p.height} cm`];
  if (p.tex !== 'lisa') parts.push(TEXTURES[p.tex].toLowerCase());
  parts.push(`${LINES[p.line].name} ${FIL[p.color].name} (${p.color})` + (p.mode === 'bicolor' ? ` + ${FIL[p.color2].name} (${p.color2})` : ''));
  if (p.watertight) parts.push('interior estanco');
  if (p.engrave) parts.push(`grabado «${p.engrave}»`);
  return parts.join(' · ');
}

/* ---------- 00c. CATÁLOGO: los modelos fijos ---------- */
const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* sin almacenamiento */ } },
  del(k) { try { localStorage.removeItem(k); } catch (e) { /* sin almacenamiento */ } },
};
const modelById = id => CATALOG.find(m => m.id === id);
/* ---------- 00d. CROMO COMÚN: cabecera, pie, cesta y cursor ----------
   Se inyectan en cada página para no repetir el marcado. */
const CHROME = {
  header: `
  <a class="pw-header__logo" href="index.html" aria-label="ARKO, inicio">ARKO</a>
  <nav class="pw-header__nav" id="pw-nav" aria-label="Principal">
    <a href="coleccion.html" data-nav="coleccion">Modelos</a>
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
    <div class="pw-footer__col"><h4>Tienda</h4><ul><li><a href="pieza.html#anfora">Ánfora</a></li><li><a href="pieza.html#monolito">Monolito</a></li><li><a href="pieza.html#estrato">Estrato</a></li><li><a href="pieza.html#onda">Onda</a></li><li><a href="taller.html">Crea el tuyo</a></li></ul></div>
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
    <div class="pw-cart__body"><p class="pw-cart__empty">Tu cesta está vacía. Elige uno de los modelos o crea el tuyo en el taller.</p><ul class="pw-cart__list"></ul></div>
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
// Lleva una configuración al taller (en otra página)
function openInTaller(params) {
  if (document.body.dataset.page === 'taller') { emit('lab:load', params); return; }
  store.set('arko-taller', params);
  location.href = 'taller.html';
}
// Añade una configuración a la cesta; el precio siempre sale de priceOf()
function addToCart(params, model) {
  const q = normalizeParams(params);
  emit('cart:add', {
    key: JSON.stringify(q), params: q, model: model ? model.id : null,
    name: model ? `${model.name} ${model.code}` : `${TYPE_NAMES[q.type]} a medida`,
    desc: describe(q), price: priceOf(q), swatch: swatchCSS(q.color), swatch2: q.mode === 'bicolor' ? swatchCSS(q.color2) : null,
  });
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
   params: { type, shape, height (cm), width, mouth, twist (°), sides (3–32; 32 = redondo),
             tex, texAmt (0–1), texN, seed, … }   1 unidad = 10 cm */
const PWForm = {
  CODES: { vase: 'V', lamp: 'L', planter: 'M', tray: 'B', candle: 'P' },
  coeffs(seed) {
    const r = mulberry32((seed * 9301 + 49297) | 0);
    return { bc: .22 + r() * .32, bw: .13 + r() * .15, bulb: .26 + r() * .24, lip: r() * .16, a2: .02 + r() * .05, f2: 1 + r() * 2.6, p2: r(), wf: 3 + Math.floor(r() * 6), wp: r() * 6.283, k: r() };
  },
  // Perfil de revolución según tipología y silueta
  profile(p, t, c) {
    const rip = c.a2 * Math.sin(Math.PI * 2 * (c.f2 * t + c.p2));
    switch (p.type) {
      case 'lamp':    return .2 + .88 * Math.pow(t, 1.15 + c.k * 1.6) + rip * .8 + .05 * smooth(.9, 1, t);
      case 'planter': return .52 + .3 * t + rip * .7 + .06 * smooth(.88, 1, t) - .05 * (1 - smooth(0, .08, t));
      case 'tray':    return .82 + .2 * smooth(0, 1, t) + rip * .25;
      case 'candle':  return .36 + .1 * Math.sin(Math.PI * t) - .06 * t + rip * .6;
    }
    switch (p.shape) {
      case 'columna': return .35 - .03 * t + rip * .4;
      case 'caliz':   return .15 + .46 * Math.pow(smooth(.08, 1, t), 1.3) + .13 * (1 - smooth(0, .1, t)) + rip * .4;
      case 'bulbo':   return .16 + .44 * Math.exp(-((t - .33) ** 2) / (2 * .17 * .17)) + .07 * smooth(.84, 1, t) + rip * .4;
      case 'cono':    return .5 - .29 * t + rip * .4;
      case 'reloj':   return .44 - .23 * Math.sin(Math.PI * t) + rip * .4;
      default: { const bulb = c.bulb * Math.exp(-((t - c.bc) ** 2) / (2 * c.bw * c.bw)); return .27 + bulb + c.lip * smooth(.78, 1, t) + rip; }
    }
  },
  radius(p, t, c) {
    let r = PWForm.profile(p, t, c) * (p.width ?? 1);
    r *= lerp(1, p.mouth ?? 1, smooth(.55, 1, t));
    return Math.max(.05, r);
  },
  // Textura de superficie (modula el radio antes de la torsión, así las estrías giran)
  surface(p, t, phi, c) {
    const tex = p.tex || (p.wave ? 'ondas' : 'lisa'), a = p.tex ? (p.texAmt ?? 0) : (p.wave || 0), n = p.texN || 16;
    switch (tex) {
      case 'ondas': return 1 + a * .14 * Math.sin(phi * c.wf + t * Math.PI * 4 + c.wp);
      case 'estrias': { const s = Math.sin(phi * n / 2); return 1 - a * .075 * s * s; }
      case 'costillas': return 1 + a * .07 * Math.pow(Math.abs(Math.cos(phi * n / 2)), 10);
      case 'relieve': { const m = Math.max(2, Math.round(n * (p.height / 10) * .32)); return 1 + a * .065 * Math.max(0, Math.sin(phi * n)) * Math.max(0, Math.sin(t * Math.PI * m)); }
      default: return 1;
    }
  },
  point(p, c, t, phi, out) {
    const H = p.height / 10;
    let r = PWForm.radius(p, t, c);
    if (p.sides < 32) { const seg = (Math.PI * 2) / p.sides; const a = ((phi % seg) + seg) % seg - seg / 2; r *= Math.cos(seg / 2) / Math.cos(a); }
    r *= PWForm.surface(p, t, phi, c);
    const ang = phi + (p.twist * Math.PI / 180) * t;
    out[0] = r * Math.cos(ang); out[1] = t * H; out[2] = r * Math.sin(ang);
    return out;
  },
  // Resolución necesaria para que las texturas finas no se pierdan
  res(p, baseU, baseV) {
    const n = p.texN || 16;
    let U = baseU, V = baseV;
    if (p.tex === 'estrias' || p.tex === 'costillas') U = Math.max(U, Math.min(320, n * 8));
    if (p.tex === 'relieve') { U = Math.max(U, Math.min(320, n * 10)); V = Math.max(V, Math.min(260, Math.round(n * (p.height / 10) * .32) * 10)); }
    if (p.sides < 32) U = p.sides * Math.max(1, Math.ceil(U / p.sides));
    return [U, V];
  },
  code(p) { return `${PWForm.CODES[p.type] || 'O'}—${pad(p.seed, 5)}`; },
};

/* ---------- 02. ESCENA 3D REALISTA ----------
   · Iluminación de estudio: mapa de entorno (PMREM) con softboxes + luz
     principal con sombra suave y sombra de contacto bajo la base.
   · Material físico por línea Bambu (mate, básico, seda, mármol, madera,
     translúcido) y colores oficiales en espacio lineal, sin curva de tono
     que los altere.
   · Capas reales de 0,2 mm como normal map (visibles al acercar la lupa).
   · Interior más oscuro (cara interna) y lámparas que se encienden. */
const lin = hex => new THREE.Color(hex).convertSRGBToLinear();
const UV_CM = .25; // las texturas cubren 4 × 4 cm
function buildFormGeometry(p, resU, resV) {
  const [U, V] = PWForm.res(p, resU, resV);
  const count = U * (V + 1) + 1, geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
  geo.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(count * 2), 2));
  geo.setAttribute('color', new THREE.BufferAttribute(new Float32Array(count * 3), 3));
  const idx = [];
  for (let j = 0; j < V; j++) for (let i = 0; i < U; i++) {
    const a = j * U + i, b = j * U + ((i + 1) % U), c = (j + 1) * U + i, d = (j + 1) * U + ((i + 1) % U);
    idx.push(a, c, b, b, c, d);
  }
  const center = U * (V + 1);
  for (let i = 0; i < U; i++) idx.push(center, i, (i + 1) % U);
  geo.setIndex(idx);
  geo.userData = { U, V };
  fillFormPositions(geo, p);
  return geo;
}
// Color por altura: liso, bicolor (cambio de filamento en una capa) o degradado del propio rollo
function colorAt(p, t, out) {
  const f = FIL[p.color] || { hex: ['#cccccc'] };
  if (f.hex.length > 1) { out.copy(lin(f.hex[0])).lerp(lin(f.hex[1]), smooth(.05, .95, t)); return out; }
  if (p.mode === 'bicolor' && FIL[p.color2]) return out.copy(lin(t < (p.split ?? .5) ? f.hex[0] : FIL[p.color2].hex[0]));
  return out.copy(lin(f.hex[0]));
}
function fillFormPositions(geo, p) {
  const { U, V } = geo.userData, c = PWForm.coeffs(p.seed), H = p.height / 10;
  const pos = geo.attributes.position.array, uv = geo.attributes.uv.array, col = geo.attributes.color.array, tmp = [0, 0, 0];
  const col3 = new THREE.Color(), R0 = .45 * (p.width ?? 1);
  let k = 0, q = 0, m = 0;
  for (let j = 0; j <= V; j++) {
    const t = j / V;
    colorAt(p, t, col3);
    for (let i = 0; i < U; i++) {
      PWForm.point(p, c, t, (i / U) * Math.PI * 2, tmp);
      pos[k++] = tmp[0]; pos[k++] = tmp[1] - H / 2; pos[k++] = tmp[2];
      uv[q++] = (i / U) * Math.PI * 2 * R0 * 10 * UV_CM; uv[q++] = t * H * 10 * UV_CM;   // en cm
      col[m++] = col3.r; col[m++] = col3.g; col[m++] = col3.b;
    }
  }
  colorAt(p, 0, col3);
  pos[k++] = 0; pos[k++] = -H / 2; pos[k++] = 0; uv[q++] = 0; uv[q++] = 0; col[m++] = col3.r; col[m++] = col3.g; col[m++] = col3.b;
  geo.attributes.position.needsUpdate = true; geo.attributes.uv.needsUpdate = true; geo.attributes.color.needsUpdate = true;
  geo.computeVertexNormals(); geo.computeBoundingSphere();
}
// Normal map de capas: 200 cordones de 0,2 mm en una tesela de 4 cm
const TEX = {};
function layerNormalMap() {
  if (TEX.layers) return TEX.layers;
  const w = 8, per = 8, h = 200 * per, cv = document.createElement('canvas'); cv.width = w; cv.height = h;
  const ctx = cv.getContext('2d'), img = ctx.createImageData(w, h), d = img.data;
  for (let y = 0; y < h; y++) {
    const s = ((y % per) + .5) / per, dh = Math.cos(Math.PI * s) * Math.PI;      // pendiente del cordón
    let ny = -dh * .32, nz = 1; const l = Math.hypot(ny, nz); ny /= l; nz /= l;
    for (let x = 0; x < w; x++) { const i = (y * w + x) * 4; d[i] = 128; d[i + 1] = Math.round((ny * .5 + .5) * 255); d[i + 2] = Math.round((nz * .5 + .5) * 255); d[i + 3] = 255; }
  }
  ctx.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return (TEX.layers = t);
}
// Mármol: moteado mineral; Madera: fibras cortas en la dirección de la capa
function speckleMap(kind) {
  if (TEX[kind]) return TEX[kind];
  const s = 512, cv = document.createElement('canvas'); cv.width = cv.height = s;
  const ctx = cv.getContext('2d'), r = mulberry32(kind === 'marble' ? 3 : 9);
  ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, s, s);
  if (kind === 'marble') {
    for (let i = 0; i < 1400; i++) { const g = 40 + r() * 110; ctx.fillStyle = `rgba(${g},${g},${g},${.35 + r() * .55})`; ctx.beginPath(); ctx.ellipse(r() * s, r() * s, .5 + r() * 1.8, .5 + r() * 1.4, r() * 3, 0, 6.3); ctx.fill(); }
  } else {
    for (let i = 0; i < 900; i++) { const g = 150 + r() * 70; ctx.fillStyle = `rgba(${g * .85},${g * .7},${g * .5},${.25 + r() * .4})`; ctx.fillRect(r() * s, r() * s, 3 + r() * 14, .6 + r() * 1.2); }
  }
  const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.encoding = THREE.sRGBEncoding;
  return (TEX[kind] = t);
}
function contactShadowMap() {
  if (TEX.contact) return TEX.contact;
  const s = 128, cv = document.createElement('canvas'); cv.width = cv.height = s;
  const ctx = cv.getContext('2d'), g = ctx.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(.45, 'rgba(0,0,0,.55)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  ctx.fillStyle = g; ctx.fillRect(0, 0, s, s);
  return (TEX.contact = new THREE.CanvasTexture(cv));
}
// Hormigón del pedestal
function makeConcreteTexture() {
  if (TEX.concrete) return TEX.concrete;
  const s = 256, cv = document.createElement('canvas'); cv.width = cv.height = s;
  const ctx = cv.getContext('2d'), img = ctx.createImageData(s, s), d = img.data, rnd = mulberry32(11);
  for (let i = 0; i < s * s; i++) { const v = 222 + (rnd() - .5) * 26; d[i * 4] = d[i * 4 + 1] = d[i * 4 + 2] = v; d[i * 4 + 3] = 255; }
  ctx.putImageData(img, 0, 0);
  for (let i = 0; i < 90; i++) { ctx.fillStyle = `rgba(90,80,70,${.25 + rnd() * .4})`; ctx.beginPath(); ctx.ellipse(rnd() * s, rnd() * s, .6 + rnd() * 2, .6 + rnd() * 1.6, 0, 0, 6.3); ctx.fill(); }
  const t = new THREE.CanvasTexture(cv); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(3, 1); t.encoding = THREE.sRGBEncoding;
  return (TEX.concrete = t);
}
// Entorno de estudio: cúpula neutra con softboxes, convertido a PMREM
function studioEnvironment(renderer) {
  const pm = new THREE.PMREMGenerator(renderer), sc = new THREE.Scene();
  const geo = new THREE.SphereGeometry(10, 48, 24), cols = [], P = geo.attributes.position;
  for (let i = 0; i < P.count; i++) { const y = P.getY(i) / 10, v = y > 0 ? lerp(.78, 1, y) : lerp(.78, .3, -y); cols.push(v, v * .99, v * .97); }
  geo.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
  sc.add(new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.BackSide })));
  const box = (w, h, x, y, z, k) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color: new THREE.Color(k, k, k), side: THREE.DoubleSide })); m.position.set(x, y, z); m.lookAt(0, 0, 0); sc.add(m); };
  box(5, 6, -6.5, 4, 4, 5);    // softbox principal (izquierda)
  box(4, 5, 7, 2.5, 3, 1.8);   // relleno
  box(9, 2.5, 0, 9, -1, 2.5);  // cenital
  box(3, 7, 2, 3, -8, 1.6);    // contraluz
  const tex = pm.fromScene(sc, .03).texture; pm.dispose();
  return tex;
}
// Propiedades físicas por línea de filamento
const LOOK = {
  matte:       { rough: .9,  metal: 0,   clear: 0,   ns: .55 },
  basic:       { rough: .42, metal: 0,   clear: .3,  ns: .45 },
  gradient:    { rough: .42, metal: 0,   clear: .3,  ns: .45 },
  silk:        { rough: .3,  metal: .55, clear: .35, ns: .35 },
  marble:      { rough: .72, metal: 0,   clear: 0,   ns: .5, map: 'marble' },
  wood:        { rough: .86, metal: 0,   clear: 0,   ns: .65, map: 'wood' },
  translucent: { rough: .25, metal: 0,   clear: .4,  ns: .3, opacity: .7 },
};

class FormStage {
  constructor(canvas, opts) {
    this.canvas = canvas;
    this.o = Object.assign({ resU: 96, resV: 120, autoRotate: .16, elev: .14, plinthH: .9, ratio: 2 }, opts);
    this.p = normalizeParams(opts.params);
    this.running = false; this.visible = false; this.view = 'solid'; this.zoom = 1;
    this.rotY = .5; this.rotVel = 0; this.elev = this.o.elev; this.targetElev = this.o.elev;
    this.build = null; this.onFrame = null; this.target = new THREE.Vector3();

    const r = this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    r.setPixelRatio(Math.min(devicePixelRatio || 1, PW.isMobile() ? 1.5 : this.o.ratio));
    r.setClearColor(0x000000, 0);
    r.outputEncoding = THREE.sRGBEncoding;
    r.toneMapping = THREE.NoToneMapping;           // sin curva de tono: el color del filamento no se desplaza
    r.shadowMap.enabled = true; r.shadowMap.type = THREE.PCFSoftShadowMap;
    r.localClippingEnabled = true;
    this.maxAniso = r.capabilities.getMaxAnisotropy();

    this.scene = new THREE.Scene();
    this.scene.environment = studioEnvironment(r);
    this.camera = new THREE.PerspectiveCamera(28, 1, .02, 100);
    const key = this.key = new THREE.DirectionalLight(0xffffff, .78);   // calibrado: la cara frontal reproduce el hex del filamento
    key.position.set(-3.4, 4.6, 2.8); key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -.0004; key.shadow.normalBias = .015; key.shadow.radius = 5;
    this.scene.add(key);

    this.plane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 999);
    const layers = layerNormalMap(); layers.anisotropy = this.maxAniso;
    this.matOuter = new THREE.MeshPhysicalMaterial({ vertexColors: true, normalMap: layers, side: THREE.FrontSide, clippingPlanes: [this.plane], envMapIntensity: .68 });
    this.matInner = new THREE.MeshPhysicalMaterial({ vertexColors: true, normalMap: layers, side: THREE.BackSide, clippingPlanes: [this.plane], envMapIntensity: .22 });
    this.matWire = new THREE.MeshBasicMaterial({ color: lin('#2A2927'), wireframe: true, transparent: true, opacity: .5, clippingPlanes: [this.plane] });
    this.matLayers = new THREE.LineBasicMaterial({ color: lin('#2A2927'), transparent: true, opacity: .75, clippingPlanes: [this.plane] });

    this.group = new THREE.Group(); this.scene.add(this.group);
    this.mesh = new THREE.Mesh(undefined, this.matOuter); this.mesh.castShadow = true; this.mesh.receiveShadow = true; this.group.add(this.mesh);
    this.inner = new THREE.Mesh(undefined, this.matInner); this.inner.receiveShadow = true; this.group.add(this.inner);
    this.layers = new THREE.LineSegments(new THREE.BufferGeometry(), this.matLayers); this.layers.visible = false; this.group.add(this.layers);
    this.ring = new THREE.LineLoop(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: lin('#9C5F38') })); this.ring.visible = false; this.group.add(this.ring);
    this.bulb = new THREE.PointLight(lin('#FFC27A'), 0, 4, 2); this.group.add(this.bulb);

    const conc = makeConcreteTexture();
    this.plinth = new THREE.Mesh(new THREE.CylinderGeometry(1, 1, 1, 96, 1), new THREE.MeshStandardMaterial({ color: lin('#C9C2B6'), map: conc, roughness: .95 }));
    this.plinth.castShadow = true; this.plinth.receiveShadow = true; this.scene.add(this.plinth);
    this.contact = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ color: 0x000000, alphaMap: contactShadowMap(), transparent: true, opacity: .55, depthWrite: false }));
    this.contact.rotation.x = -Math.PI / 2; this.contact.position.y = .002; this.scene.add(this.contact);
    this.floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.ShadowMaterial({ opacity: .18 }));
    this.floor.rotation.x = -Math.PI / 2; this.floor.receiveShadow = true; this.scene.add(this.floor);

    this.regenerate(true); this.applyLook();
    this.loop = this.loop.bind(this);
    this.resize();
    if ('ResizeObserver' in window) new ResizeObserver(() => this.resize()).observe(canvas.parentElement);
    else addEventListener('resize', () => this.resize());
    watchVisible(canvas.parentElement, v => { this.visible = v; this.sync(); }, '0px');
    document.addEventListener('visibilitychange', () => this.sync());
  }
  setParams(q, rebuild) { this.p = normalizeParams(Object.assign({}, this.p, q)); this.regenerate(rebuild); this.applyLook(); }
  regenerate(rebuild) {
    const g0 = this.mesh.geometry, [U, V] = PWForm.res(this.p, this.o.resU, this.o.resV);
    if (rebuild || !g0 || g0.userData.U !== U || g0.userData.V !== V) {
      if (g0) g0.dispose();
      const g = buildFormGeometry(this.p, this.o.resU, this.o.resV);
      this.mesh.geometry = g; this.inner.geometry = g;
      const rg = new THREE.BufferGeometry(); rg.setAttribute('position', new THREE.BufferAttribute(new Float32Array(g.userData.U * 3), 3));
      this.ring.geometry.dispose(); this.ring.geometry = rg;
    } else fillFormPositions(g0, this.p);
    if (this.view === 'layers') this.buildLayerLines();
    this.fit();
  }
  // Material según la línea Bambu elegida
  applyLook() {
    const L = LOOK[this.p.line] || LOOK.matte, lit = this.p.type === 'lamp' && this.p.lit;
    [this.matOuter, this.matInner].forEach((m, i) => {
      m.roughness = L.rough; m.metalness = L.metal; m.clearcoat = L.clear; m.clearcoatRoughness = .35;
      m.normalScale.set(L.ns, L.ns);
      m.map = L.map ? speckleMap(L.map) : null;
      m.transparent = !!L.opacity; m.opacity = L.opacity || 1; m.depthWrite = !L.opacity;
      m.color.setScalar(i ? .62 : 1);                             // la cara interna recibe menos luz
      m.emissive.copy(lin(lit ? '#FFB868' : '#000000'));
      m.emissiveIntensity = lit ? (i ? .9 : (L.opacity ? .55 : .12)) : 0;
      m.needsUpdate = true;
    });
    this.bulb.intensity = lit ? 2.2 : 0;
    this.renderOnce();
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
  setView(v) {
    this.view = v;
    this.mesh.visible = v !== 'layers'; this.inner.visible = v === 'solid';
    this.mesh.material = v === 'wire' ? this.matWire : this.matOuter;
    this.mesh.castShadow = v === 'solid';
    this.layers.visible = v === 'layers';
    if (v === 'layers') this.buildLayerLines();
    this.renderOnce();
  }
  setZoom(z) { this.zoom = clamp(z, 1, 7); this.fit(); this.sync(); this.renderOnce(); }
  fit() {
    const pos = this.mesh.geometry.attributes.position.array;
    let m = 0; for (let i = 0; i < pos.length; i += 3) m = Math.max(m, pos[i] * pos[i] + pos[i + 2] * pos[i + 2]);
    const maxR = this.maxR = Math.sqrt(m), H = this.H = this.p.height / 10, ph = this.o.plinthH;
    const pr = maxR * 1.16 + .06;
    this.group.position.y = H / 2;
    this.bulb.position.set(0, -H / 2 + H * .38, 0);
    this.plinth.scale.set(pr, ph, pr); this.plinth.position.y = -ph / 2;
    this.contact.scale.set(maxR * 2.5, maxR * 2.5, 1);
    this.floor.position.y = -ph;
    const sc = this.key.shadow.camera, ext = Math.max(pr * 2.4, H * 1.2, 2.5);
    sc.left = -ext; sc.right = ext; sc.top = ext; sc.bottom = -ext; sc.near = .5; sc.far = 30; sc.updateProjectionMatrix();
    const total = H + ph, z = this.zoom;
    // Al acercar, el encuadre sube hacia el tercio alto de la pieza (donde mejor se ven las capas)
    this.target.set(0, lerp((H - ph) / 2 + total * .03, H * .62, smooth(1, 2.5, z)), 0);
    const tan = Math.tan((this.camera.fov * Math.PI) / 360), aspect = this.camera.aspect || 1;
    const needV = (total / 2) * 1.24 / tan, needH = pr * 1.55 / (tan * aspect);
    this.targetDist = (Math.max(needV, needH) + pr) / z;
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
    this.rotY += (PW.reduced || this.zoom > 1.2 ? 0 : this.o.autoRotate) * dt + this.rotVel * dt;
    this.rotVel *= Math.pow(.05, dt);
    this.elev = lerp(this.elev, this.targetElev, 1 - Math.pow(.002, dt));
    this.dist = lerp(this.dist, this.targetDist, 1 - Math.pow(.01, dt));
    this.renderOnce();
  }
}
function webglFallback(host) { const d = document.createElement('div'); d.className = 'pw-fallback'; d.textContent = 'La vista 3D no está disponible en este navegador.'; host.appendChild(d); }
// Arrastrar para girar, rueda/pellizco/botones para acercar
function orbitControls(stage, el) {
  let drag = null, pinch = null;
  const pts = new Map();
  el.addEventListener('pointerdown', e => { pts.set(e.pointerId, e); el.setPointerCapture(e.pointerId); drag = { x: e.clientX, y: e.clientY }; });
  el.addEventListener('pointermove', e => {
    if (!pts.has(e.pointerId)) return;
    pts.set(e.pointerId, e);
    if (pts.size === 2) {
      const [a, b] = [...pts.values()], d = Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
      if (pinch) stage.setZoom(stage.zoom * d / pinch); pinch = d; return;
    }
    if (!drag) return;
    const dx = e.clientX - drag.x, dy = e.clientY - drag.y; drag = { x: e.clientX, y: e.clientY };
    stage.rotY += dx * .01; stage.rotVel = dx * .5; stage.targetElev = clamp(stage.targetElev + dy * .004, -.1, .9);
  });
  const end = e => { pts.delete(e.pointerId); pinch = null; if (!pts.size) drag = null; };
  el.addEventListener('pointerup', end); el.addEventListener('pointercancel', end);
  el.addEventListener('wheel', e => { if (!e.ctrlKey && Math.abs(e.deltaY) < 40 && stage.zoom === 1) return; e.preventDefault(); stage.setZoom(stage.zoom * (e.deltaY < 0 ? 1.15 : 1 / 1.15)); }, { passive: false });
}
// Imagen fija de una configuración (tarjetas de la colección): mismo motor, mismo material
let snapStage = null;
function snapshot(params, opts = {}) {
  if (!PW.hasThree) return null;
  try {
    if (!snapStage) {
      const host = document.createElement('div');
      host.style.cssText = 'position:fixed;left:-10000px;top:0;width:520px;height:680px;pointer-events:none';
      const cv = document.createElement('canvas'); host.append(cv); document.body.append(host);
      snapStage = new FormStage(cv, { params, resU: 128, resV: 170, ratio: 1.5, elev: .13 });
    }
    snapStage.setParams(Object.assign({}, params, { lit: opts.lit ?? params.type === 'lamp' }), true);
    snapStage.rotY = opts.rotY ?? .55; snapStage.dist = snapStage.targetDist;
    snapStage.renderOnce();
    return snapStage.renderer.domElement.toDataURL('image/webp', .9);
  } catch (e) { return null; }
}

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
  const model = CATALOG[0];
  const base = Object.assign({}, model.params, { tex: 'ondas', texAmt: .1 });
  const stage = new FormStage(canvas, { params: base, resU: PW.isMobile() ? 64 : 96, resV: PW.isMobile() ? 90 : 140, autoRotate: .14, elev: .12 });
  const twistOut = $('[data-hero-twist]'), diamOut = $('[data-hero-diam]'), filOut = $('[data-hero-fil]');
  if (diamOut) diamOut.textContent = Math.round(stage.maxR * 20);
  if (filOut) filOut.textContent = `${LINES[base.line].name} ${FIL[base.color].name}`;
  let mx = 0, my = 0, frame = 0;
  if (PW.fine) addEventListener('pointermove', e => { mx = e.clientX / innerWidth * 2 - 1; my = e.clientY / innerHeight * 2 - 1; }, { passive: true });
  const cur = { twist: base.twist, amt: base.texAmt };
  stage.onFrame = (dt, now) => {
    if (PW.reduced) return;
    // El puntero modela la pieza: X → torsión, Y → ondulación
    const auto = PW.fine ? 0 : Math.sin(now / 2600);
    const tT = base.twist + (mx + auto) * 90, tA = clamp((PW.fine ? (1 - (my + 1) / 2) : .5 + .5 * Math.sin(now / 3100)) * .45, 0, 1);
    const k = 1 - Math.pow(.05, dt), nt = lerp(cur.twist, tT, k), na = lerp(cur.amt, tA, k);
    if (Math.abs(nt - cur.twist) > .05 || Math.abs(na - cur.amt) > .001) { cur.twist = nt; cur.amt = na; stage.p.twist = nt; stage.p.texAmt = na; fillFormPositions(stage.mesh.geometry, stage.p); }
    stage.targetElev = .12 + my * .06;
    if (twistOut && ++frame % 10 === 0) twistOut.textContent = Math.round(cur.twist);
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

/* ---------- 09. TALLER: el cliente crea su pieza ---------- */
// Muestras de color: el hex oficial de Bambu Lab, sin sombreados encima
function swatchesHTML(line, selected, exclude) {
  return FILAMENTS.filter(f => f.line === line && f.code !== exclude).map(f =>
    `<button type="button" class="pw-swatch${f.hex.length > 1 ? ' is-gradient' : ''}${line === 'translucent' ? ' is-translucent' : ''}" data-code="${f.code}" style="--sw:${line === 'translucent' ? translucentCSS(f.hex[0]) : swatchCSS(f.code)}" aria-pressed="${f.code === selected}" aria-label="${esc(f.name)} · ${f.code}" title="${esc(f.name)} · ${f.code}"></button>`).join('');
}
// Translúcido: Bambu publica estos colores con 50 % de opacidad (#RRGGBB80)
const translucentCSS = hex => { const [r, g, b] = hexRGB(hex); return `linear-gradient(rgba(${r},${g},${b},.5),rgba(${r},${g},${b},.5))`; };
const filamentHTML = code => `<i style="background:${swatchCSS(code)}"></i><span>${esc(filLabel(code))}<small>${FIL[code].hex.join(' → ')}</small></span>`;
function estimateOf(geo, p) {
  let area = 0;
  if (geo) {
    const P = geo.attributes.position.array, I = geo.index.array;
    for (let i = 0; i < I.length; i += 3) {
      const a = I[i] * 3, b = I[i + 1] * 3, c = I[i + 2] * 3;
      const ux = P[b] - P[a], uy = P[b + 1] - P[a + 1], uz = P[b + 2] - P[a + 2], vx = P[c] - P[a], vy = P[c + 1] - P[a + 1], vz = P[c + 2] - P[a + 2];
      const cx = uy * vz - uz * vy, cy = uz * vx - ux * vz, cz = ux * vy - uy * vx; area += Math.sqrt(cx * cx + cy * cy + cz * cz) / 2;
    }
  } else area = p.height / 10 * 3.4;
  const grams = area * 100 * (p.watertight ? .16 : .12) * 1.24, hours = grams / 11;
  return { grams, hours };
}
const fmtTime = h => `${Math.floor(h)} h ${pad(Math.round((h % 1) * 60) % 60, 2)} min`;

function initLab() {
  const root = $('.pw-lab'); if (!root) return;
  const canvas = $('.pw-lab__canvas', root), form = $('.pw-lab__panel', root), json = $('[data-lab-json]', root), details = $('.pw-lab__json', root);
  const outs = {}; $$('[data-lab-out]', root).forEach(e => (outs[e.dataset.labOut] = e));
  if (PW.isMobile()) details.open = false;
  let model = CATALOG[0], p = normalizeParams(Object.assign({}, model.params, { lit: true }));
  const incoming = store.get('arko-taller');
  if (incoming) { model = modelById(incoming.__model) || null; delete incoming.__model; p = normalizeParams(Object.assign({ lit: true }, incoming)); store.del('arko-taller'); }
  let stage = null; const prev = {};

  // Controles generados desde los datos
  const chips = (sel, obj, attr) => { $(sel, form).innerHTML = Object.entries(obj).map(([k, v]) => `<button type="button" data-${attr}="${k}" aria-pressed="false">${v}</button>`).join(''); };
  chips('[data-types]', TYPE_NAMES, 'type'); chips('[data-shapes]', SHAPES, 'shape'); chips('[data-texes]', TEXTURES, 'tex');
  $('[data-lines]', form).innerHTML = Object.entries(LINES).map(([k, l]) => `<button type="button" data-line="${k}" aria-pressed="false">${l.short}${l.fee ? ` <small>+${l.fee} €</small>` : ''}</button>`).join('');
  $('[data-models]', form).innerHTML = CATALOG.map(m => `<button type="button" class="pw-model" data-model="${m.id}" aria-pressed="false"><span class="pw-model__img"><img alt="" data-snap="${m.id}"></span><span>${esc(m.name)}</span></button>`).join('')
    + `<button type="button" class="pw-model" data-model="cero" aria-pressed="false"><span class="pw-model__img pw-model__img--blank">+</span><span>Desde cero</span></button>`;
  $$('[data-snap]', form).forEach(img => { const m = modelById(img.dataset.snap); snapInto(img, m.id, m.params); });
  $('[data-delivery]', root).textContent = deliveryWindow();
  $$('[data-fee]', form).forEach(e => (e.textContent = `+${PRICING[e.dataset.fee]} €`));

  if (PW.hasThree) {
    stage = new FormStage(canvas, { params: p, resU: PW.isMobile() ? 64 : 112, resV: PW.isMobile() ? 90 : 150, autoRotate: .2, elev: .16 });
    stage.plane.constant = -99;
    orbitControls(stage, canvas);
    let built = false;
    watchVisible(canvas.parentElement, v => { if (v && !built) { built = true; stage.startBuild(2800); } }, '-15% 0px');
    stage.onFrame = () => { const pr = stage.build ? stage.buildProgress || 0 : 1; outs.progress.style.width = (pr * 100) + '%'; outs.status.textContent = pr < 1 ? `Imprimiendo ${Math.round(pr * 100)}%` : 'Lista'; };
    const zoomOut = $('[data-zoom-val]', root);
    $$('[data-zoom]', root).forEach(b => b.addEventListener('click', () => { stage.setZoom(stage.zoom * (b.dataset.zoom === 'in' ? 1.7 : 1 / 1.7)); zoomOut.textContent = stage.zoom.toFixed(1).replace('.', ',') + '×'; }));
    $$('[data-view]', root).forEach(b => b.addEventListener('click', () => { $$('[data-view]', root).forEach(x => x.setAttribute('aria-pressed', x === b)); stage.setView(b.dataset.view); }));
  } else webglFallback(canvas.parentElement);

  const OUT = {
    height: v => `${v} cm`, width: v => `${Math.round(v * 100)} %`, mouth: v => `${Math.round(v * 100)} %`, texAmt: v => `${Math.round(v * 100)} %`,
    texN: v => v, twist: v => `${v}°`, sides: v => (v >= 32 ? 'redondo' : v), seed: v => pad(v, 5), split: v => `${Math.round(v * 100)} %`,
  };
  const press = (attr, val) => $$(`[data-${attr}]`, form).forEach(b => b.setAttribute('aria-pressed', String(b.dataset[attr] === String(val))));
  const show = (sel, ok) => $$(sel, form).forEach(e => (e.hidden = !ok));
  const syncUI = () => {
    $$('input[type="range"]', form).forEach(inp => { inp.value = p[inp.name]; const o = $(`[data-out="${inp.name}"]`, form); if (o) o.textContent = OUT[inp.name](p[inp.name]); });
    press('type', p.type); press('shape', p.shape); press('tex', p.tex); press('line', p.line); press('mode', p.mode); press('model', model ? model.id : '');
    show('[data-only="vase"]', p.type === 'vase'); show('[data-only="lamp"]', p.type === 'lamp'); show('[data-only-water]', p.type === 'vase' || p.type === 'planter');
    show('[data-show="texAmt"]', p.tex !== 'lisa'); show('[data-show="texN"]', ['estrias', 'costillas', 'relieve'].includes(p.tex));
    show('[data-color-mode]', p.line !== 'gradient'); show('[data-bicolor]', p.mode === 'bicolor');
    $('[data-swatches]', form).innerHTML = swatchesHTML(p.line, p.color);
    $('[data-swatches2]', form).innerHTML = p.mode === 'bicolor' ? swatchesHTML(p.line, p.color2, p.color) : '';
    $('[data-line-note]', form).textContent = LINES[p.line].note;
    $('[data-filament]', form).innerHTML = filamentHTML(p.color) + (p.mode === 'bicolor' ? filamentHTML(p.color2) : '');
    $('#pw-water').checked = !!p.watertight; $('#pw-lit').checked = !!p.lit;
    const eng = $('#pw-engrave'); if (document.activeElement !== eng) eng.value = p.engrave;
  };
  const renderJSON = est => {
    const f1 = FIL[p.color], f2 = FIL[p.color2];
    const data = {
      modelo: model ? `${model.code} ${model.name}` : 'A medida', tipo: TYPE_NAMES[p.type], silueta: p.type === 'vase' ? SHAPES[p.shape] : '—',
      alto_cm: p.height, anchura: OUT.width(p.width), boca: OUT.mouth(p.mouth), torsion: p.twist, lados: p.sides >= 32 ? 'redondo' : p.sides,
      superficie: TEXTURES[p.tex] + (p.tex !== 'lisa' ? ` ${OUT.texAmt(p.texAmt)}` : ''), seed: p.seed,
      filamento: `${LINES[p.line].name} ${f1.name} (${f1.code})`,
      ...(p.mode === 'bicolor' ? { filamento_2: `${f2.name} (${f2.code})`, cambio_en_capa: Math.round(p.split * p.height * 50) } : {}),
      capas: Math.round(p.height * 50), interior_estanco: !!p.watertight, grabado: p.engrave || '—',
      estimacion: { peso_g: Math.round(est.grams), impresion: fmtTime(est.hours), precio_eur: priceOf(p), plazo: '7 días + envío' },
    };
    const v = (k, val) => { const s = JSON.stringify(val), ch = prev[k] !== undefined && prev[k] !== s ? ' pw-json-changed' : ''; prev[k] = s; return `<span class="pw-json-v${ch}">${esc(s)}</span>`; };
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
  const update = (rebuild, animate) => {
    p = normalizeParams(p);
    if (stage) { stage.setParams(p, rebuild); if (animate) stage.startBuild(1500); }
    const est = estimateOf(stage && stage.mesh.geometry, p);
    outs.code.textContent = model ? `${model.code} ${model.name}${JSON.stringify(normalizeParams(model.params)) === JSON.stringify(Object.assign({}, p, { lit: undefined })) ? '' : ' · personalizado'}` : 'A medida';
    outs.verts.textContent = stage ? fmt(stage.mesh.geometry.attributes.position.count) : '—';
    outs.weight.textContent = Math.round(est.grams) + ' g'; outs.time.textContent = fmtTime(est.hours);
    outs.price.textContent = `${priceOf(p)} €`;
    renderJSON(est);
  };

  form.addEventListener('input', e => {
    const t = e.target;
    if (t.type === 'range') {
      p[t.name] = ['width', 'mouth', 'texAmt', 'split'].includes(t.name) ? parseFloat(t.value) : parseInt(t.value, 10);
      $(`[data-out="${t.name}"]`, form).textContent = OUT[t.name](p[t.name]);
      if (t.name === 'split') { update(false, false); return; }
      if (!update.raf) update.raf = requestAnimationFrame(() => { update.raf = 0; update(false, false); });
    } else if (t.id === 'pw-engrave') { p.engrave = cleanEngrave(t.value); if (t.value !== p.engrave) t.value = p.engrave; update(false, false); }
  });
  form.addEventListener('change', e => {
    if (e.target.id === 'pw-water') { p.watertight = e.target.checked; update(false, false); }
    if (e.target.id === 'pw-lit') { p.lit = e.target.checked; update(false, false); }
  });
  form.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b || !form.contains(b)) return;
    const d = b.dataset;
    if (d.model) {
      if (d.model === 'cero') { model = null; p = normalizeParams({ type: 'vase', shape: 'organica', height: 24, width: 1, mouth: 1, twist: 0, sides: 32, tex: 'lisa', texAmt: .5, texN: 16, seed: 1 + Math.floor(Math.random() * 99999), line: p.line, color: p.color, mode: 'solid', lit: true }); }
      else { model = modelById(d.model); p = normalizeParams(Object.assign({}, model.params, { lit: true })); }
      syncUI(); update(true, true); emit('generated'); return;
    }
    if (d.type) {
      p.type = d.type;
      if (p.type === 'tray' && p.height > 12) p.height = 6;
      if (p.type === 'candle' && p.height > 16) p.height = 10;
      if ((p.type === 'vase' || p.type === 'lamp') && p.height < 14) p.height = 24;
      syncUI(); update(true, true); emit('generated'); return;
    }
    if (d.shape) { p.shape = d.shape; syncUI(); update(false, false); return; }
    if (d.tex) { p.tex = d.tex; if (p.tex !== 'lisa' && p.texAmt < .2) p.texAmt = .6; syncUI(); update(false, false); return; }
    if (d.line) { p.line = d.line; p = normalizeParams(p); syncUI(); update(false, false); return; }
    if (d.mode) { p.mode = d.mode; p = normalizeParams(p); syncUI(); update(false, false); return; }
    if (d.code) { if (b.closest('[data-swatches2]')) p.color2 = d.code; else p.color = d.code; p = normalizeParams(p); syncUI(); update(false, false); return; }
    if (d.action === 'randomize') { p.seed = 1 + Math.floor(Math.random() * 99999); syncUI(); update(true, true); emit('generated'); return; }
    if (d.action === 'order') { addToCart(p, model); return; }
  });
  on('lab:load', q => {
    model = modelById(q.__model) || null; p = normalizeParams(Object.assign({ lit: true }, q));
    syncUI(); update(true, true);
    $('.pw-lab__grid', root).scrollIntoView({ behavior: PW.reduced ? 'auto' : 'smooth' });
  });
  const copyBtn = $('[data-action="copy"]', root);
  const doCopy = e => {
    e.preventDefault(); e.stopPropagation();
    const txt = JSON.stringify(renderJSON(estimateOf(stage && stage.mesh.geometry, p)), null, 2);
    const ok = () => { copyBtn.textContent = 'Copiado'; setTimeout(() => (copyBtn.textContent = 'Copiar'), 1500); };
    const fallback = () => { const r = document.createRange(); r.selectNodeContents(json); const s = getSelection(); s.removeAllRanges(); s.addRange(r); };
    try { navigator.clipboard.writeText(txt).then(ok, fallback); } catch (err) { fallback(); }
  };
  copyBtn.addEventListener('click', doCopy);
  copyBtn.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') doCopy(e); });
  syncUI(); update(false, false);
}

/* ---------- 10. DIBUJOS: render plano (reserva) y sección constructiva ---------- */
const hexRGB = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const mixHex = (a, b, t) => '#' + hexRGB(a).map((v, i) => Math.round(v + (hexRGB(b)[i] - v) * t).toString(16).padStart(2, '0')).join('');
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
    const base = (FIL[p.color] || { hex: ['#C9C2B6'] }).hex[0], md = base, dk = mixHex(base, '#000000', .45), lt = mixHex(base, '#ffffff', .35);
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
/* ---------- 10b. FOTOS DE PRODUCTO Y TARJETAS ----------
   Las tarjetas muestran una imagen renderizada con el mismo motor 3D y el
   mismo material que el taller (se guarda en la sesión para no repetirla). */
const snapCache = {}, snapJobs = [];
let snapBusy = false;
function snapInto(img, key, params, opts) {
  if (!PW.hasThree || !img) return;
  const ck = 'arko-snap-v2-' + key + '-' + JSON.stringify(params).length;
  const apply = url => { if (url) { img.src = url; img.classList.add('is-ready'); } };
  try { const c = snapCache[ck] || sessionStorage.getItem(ck); if (c) { snapCache[ck] = c; return apply(c); } } catch (e) { /* sin almacenamiento */ }
  snapJobs.push(() => { const url = snapshot(params, opts); snapCache[ck] = url; try { if (url) sessionStorage.setItem(ck, url); } catch (e) { /* cuota llena */ } apply(url); });
  if (snapBusy) return;
  snapBusy = true;
  const step = () => { const job = snapJobs.shift(); if (!job) { snapBusy = false; return; } job(); setTimeout(step, 30); };
  setTimeout(step, 80);
}
function modelCardHTML(m, span) {
  const p = m.params, f = FIL[p.color];
  return `<article class="pw-piece" style="--span:${span};--ar:${span >= 6 ? '1/1' : '3/4.2'}" data-id="${m.id}">
    <a class="pw-piece__niche pw-plaster" href="pieza.html#${m.id}" data-cursor="Ver" aria-label="${esc(m.name)}">
      <div class="pw-piece__render"><img class="pw-piece__img" alt="${esc(m.name)} en ${esc(LINES[p.line].name)} ${esc(f.name)}" data-snap="${m.id}">${pieceSVG(p, 'render')}</div>
      <div class="pw-piece__section"></div>
      <span class="pw-piece__tag">${esc(m.tag)}</span>
    </a>
    <div class="pw-piece__row"><span class="pw-piece__code">${m.code}</span><span class="pw-piece__price">${priceOf(p)} €</span></div>
    <h3 class="pw-piece__name"><a href="pieza.html#${m.id}">${esc(m.name)}</a></h3>
    <p class="pw-piece__desc"><i style="background:${swatchCSS(p.color)}"></i>${TYPE_NAMES[p.type]} · ${p.height} cm · ${esc(LINES[p.line].name)} ${esc(f.name)}</p>
    <p class="pw-piece__lead">Preparación 7 días + envío</p>
    <div class="pw-piece__actions"><button class="pw-btn pw-btn--sm" type="button" data-add data-magnetic>Añadir</button><button class="pw-btn pw-btn--sm pw-btn--line" type="button" data-customize data-magnetic>Personalizar</button></div>
  </article>`;
}
function renderCards(grid, models, spans) {
  grid.innerHTML = models.map((m, i) => modelCardHTML(m, spans[i % spans.length])).join('');
  const cards = $$('.pw-piece', grid);
  cards.forEach((c, i) => { c.classList.add('pw-enter'); c.style.setProperty('--d', i * 80 + 'ms'); });
  requestAnimationFrame(() => requestAnimationFrame(() => cards.forEach(c => c.classList.add('is-in'))));
  $$('[data-snap]', grid).forEach(img => { const m = modelById(img.dataset.snap); snapInto(img, m.id, m.params); });
  if (grid._pwBound) return;
  grid._pwBound = true;
  const modelOf = el => modelById(el.closest('.pw-piece').dataset.id);
  grid.addEventListener('click', e => {
    if (e.target.closest('[data-add]')) { const m = modelOf(e.target); addToCart(m.params, m); }
    else if (e.target.closest('[data-customize]')) { const m = modelOf(e.target); openInTaller(Object.assign({}, m.params, { __model: m.id })); }
  });
  const makeSection = e => {
    const card = e.target.closest && e.target.closest('.pw-piece'); if (!card) return;
    const sec = $('.pw-piece__section', card);
    if (!sec.firstChild) sec.innerHTML = pieceSVG(modelOf(card).params, 'section');
  };
  grid.addEventListener('pointerover', makeSection); grid.addEventListener('focusin', makeSection);
}
function initCollection() {
  const grid = $('[data-collection]'); if (!grid) return;
  renderCards(grid, CATALOG, [6, 6, 6, 6]);
}
function initFeatured() {
  const grid = $('[data-featured]'); if (!grid) return;
  renderCards(grid, CATALOG, [3, 3, 3, 3]);
}
function initDoors() {
  const col = $('[data-door="coleccion"]');
  if (col) { const m = modelById('monolito') || CATALOG[0]; col.innerHTML = `<img class="pw-door__img" alt="">${pieceSVG(m.params, 'render')}`; snapInto($('img', col), m.id, m.params); }
  const dots = $('[data-door="taller"]');
  if (dots) dots.innerHTML = `<span class="pw-door__dots">${FILAMENTS.filter(f => f.line === 'matte').slice(0, 15).map(f => `<i style="background:${f.hex[0]}" title="${esc(f.name)}"></i>`).join('')}</span>`;
}
function maxDiameterCm(p) {
  const c = PWForm.coeffs(p.seed), tmp = [0, 0, 0]; let m = 0;
  for (let j = 0; j <= 40; j++) for (let i = 0; i < 64; i++) { PWForm.point(p, c, j / 40, i / 64 * Math.PI * 2, tmp); m = Math.max(m, Math.hypot(tmp[0], tmp[2])); }
  return Math.round(m * 20);
}
// Página de pieza: pieza.html#anfora — el cliente puede cambiarle el color aquí mismo
function initPieza() {
  const root = $('[data-pieza]'); if (!root) return;
  const canvas = $('.pw-product__canvas', root), out = {};
  $$('[data-p]').forEach(e => (out[e.dataset.p] = e)); // la sección constructiva está fuera de root
  let stage = null, model = null, cur = null;
  const paintColor = () => {
    out.lines.innerHTML = Object.entries(LINES).map(([k, l]) => `<button type="button" data-line="${k}" aria-pressed="${k === cur.line}">${l.short}${l.fee ? ` <small>+${l.fee} €</small>` : ''}</button>`).join('');
    out.swatches.innerHTML = swatchesHTML(cur.line, cur.color);
    out.filament.innerHTML = filamentHTML(cur.color);
    out.price.textContent = priceOf(cur) + ' €';
    const changed = cur.color !== model.params.color || cur.line !== model.params.line;
    out.colornote.textContent = changed ? 'Color elegido por ti.' : 'Color de serie.';
  };
  const show = () => {
    model = modelById(location.hash.slice(1)) || CATALOG[0];
    cur = normalizeParams(Object.assign({}, model.params, { lit: true }));
    document.title = `${model.name} · ARKO`;
    out.family.textContent = `Modelos · ${model.code}`;
    out.name.textContent = model.name; out.code.textContent = model.code; out.tag.textContent = model.tag; out.desc.textContent = model.desc;
    const p = model.params;
    out.spec.innerHTML = [['Tipo', TYPE_NAMES[p.type] + (p.type === 'vase' ? ' · ' + SHAPES[p.shape] : '')], ['Alto', p.height + ' cm'], ['Ø máximo', maxDiameterCm(p) + ' cm'], ['Superficie', TEXTURES[p.tex]],
      ['Torsión', p.twist + '°'], ['Lados', p.sides >= 32 ? 'Redondo' : p.sides], ['Capa', '0,2 mm · ' + Math.round(p.height * 50) + ' capas'], ['Seed', pad(p.seed, 5)]]
      .map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
    out.delivery.textContent = deliveryWindow();
    out.section.innerHTML = pieceSVG(p, 'section');
    paintColor();
    renderCards($('[data-related]'), CATALOG.filter(m => m.id !== model.id), [4, 4, 4]);
    if (stage) { stage.setParams(cur, true); stage.startBuild(1800); }
  };
  show();
  if (PW.hasThree && canvas) {
    try {
      stage = new FormStage(canvas, { params: cur, resU: PW.isMobile() ? 64 : 112, resV: PW.isMobile() ? 90 : 160, autoRotate: .18, elev: .14 });
      stage.plane.constant = -99; stage.renderOnce();
      on('ready', () => stage.startBuild(2600));
      orbitControls(stage, canvas);
      const zoomOut = $('[data-zoom-val]', root);
      $$('[data-zoom]', root).forEach(b => b.addEventListener('click', () => { stage.setZoom(stage.zoom * (b.dataset.zoom === 'in' ? 1.7 : 1 / 1.7)); zoomOut.textContent = stage.zoom.toFixed(1).replace('.', ',') + '×'; }));
    } catch (e) { webglFallback(canvas.parentElement); }
  } else if (canvas) webglFallback(canvas.parentElement);
  root.addEventListener('click', e => {
    const b = e.target.closest('button'); if (!b) return;
    if (b.dataset.line) { cur.line = b.dataset.line; cur = normalizeParams(cur); }
    else if (b.dataset.code) { cur.color = b.dataset.code; cur = normalizeParams(cur); }
    else return;
    paintColor(); if (stage) stage.setParams(cur, false);
  });
  addEventListener('hashchange', () => { show(); scrollTo({ top: 0, behavior: PW.reduced ? 'auto' : 'smooth' }); });
  $('[data-p-add]', root).addEventListener('click', () => addToCart(cur, model));
  const toTaller = e => { if (e) e.preventDefault(); openInTaller(Object.assign({}, cur, { __model: model.id })); };
  $('[data-p-custom]', root).addEventListener('click', () => toTaller());
  const link = $('[data-p-custom-link]', root); if (link) link.addEventListener('click', toTaller);
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
  // Solo configuraciones con el formato actual (filamento Bambu); precio siempre recalculado
  items = (Array.isArray(items) ? items : []).filter(i => i && i.params && i.params.line && FIL[i.params.color]).map(i => Object.assign(i, { price: priceOf(normalizeParams(i.params)) }));
  const save = () => { try { localStorage.setItem('arko-cesta', JSON.stringify(items)); } catch (e) { /* sin almacenamiento */ } };
  const count = () => items.reduce((n, i) => n + i.qty, 0);
  const render = () => {
    list.innerHTML = items.map((it, i) => `
      <li class="pw-cart__item">
        <span class="pw-cart__thumb"><i style="background:${it.swatch2 ? `linear-gradient(0deg, ${it.swatch} 0 50%, ${it.swatch2} 50% 100%)` : it.swatch}"></i></span>
        <div>
          <p class="pw-cart__name">${esc(it.name)}</p>
          <p class="pw-cart__desc">${esc(it.desc)}</p>
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
        body: JSON.stringify({ items: items.map(i => ({ model: i.model, params: i.params, qty: i.qty })) }),
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
