/*!
 * Only Cards Booster v1.0
 * Mejoras de conversión, confianza y SEO para la tienda Odoo de only-cards.com.
 *
 * Instalación: Sitio web → Editar → Tema → Avanzado → «Inyección de código»
 * (o Ajustes del sitio web → Código personalizado) y pegar en «Fin de <body>»:
 *
 *   <script src="/ruta/only-cards-booster.js" defer></script>
 *
 * o pegar el contenido entero entre <script>…</script>. No necesita librerías.
 * Cada módulo se puede apagar desde CONFIG. Si un selector de Odoo cambia,
 * el módulo afectado simplemente no hace nada: nunca rompe la tienda.
 */
(function () {
  "use strict";

  /* ------------------------------------------------------------------ */
  /* CONFIGURACIÓN — todo lo que el dueño puede querer cambiar           */
  /* ------------------------------------------------------------------ */
  var CONFIG = window.ONLY_CARDS_BOOSTER_CONFIG || {};
  var DEFAULTS = {
    whatsapp: "34634220287",
    email: "info@only-cards.com",
    instagram: "https://www.instagram.com/", // poner la URL real del perfil
    envio: "Envío en 2-3 días laborables",
    devolucion: "Devolución en 15 días",
    // Umbral de envío gratis en €. null = no se muestra la barra (definir con el dueño).
    envioGratisDesde: null,
    // Punto de recogida (Click & Collect) que ya existe en Odoo pero no se ve en la web.
    recogida: {
      nombre: "Only Cards", calle: "Calle Colombia 25 - bajo", ciudad: "Vigo", cp: "36204", provincia: "Pontevedra", pais: "ES",
      lat: 42.1986395, lng: -8.727956,
      // Horario de recogida tal y como está configurado en Odoo.
      horario: [["Thursday", "17:15", "20:15"], ["Friday", "17:30", "20:30"], ["Saturday", "10:30", "14:30"]],
      textoHorario: "jue 17:15–20:15 · vie 17:30–20:30 · sáb 10:30–14:30"
    },
    modulos: {
      barraAnuncios: true,
      hero: true,
      filtrosFranquicia: true,
      insignias: true,
      avisoAgotado: true,
      preventa: true,
      confianzaProducto: true,
      precioPorSobre: true,
      barraMovilCompra: true,
      vistosRecientemente: true,
      whatsappFlotante: true,
      seo: true,
      corregirTextos: true,
      barraEnvioGratis: true
    },
    // Reglas para clasificar productos por su nombre (la tienda no tiene categorías).
    franquicias: [
      { id: "pokemon", nombre: "Pokémon", patron: /pok[eé]mon|dominio delta|delta reign|\bmew\b|mewtwo|ditto|espeon|umbreon|sylveon|greninja|pikachu|charizard/i },
      { id: "yugioh", nombre: "Yu-Gi-Oh!", patron: /yu[\s-]?gi[\s-]?oh|magnificent maestros|\bkonami\b/i },
      { id: "riftbound", nombre: "Riftbound", patron: /riftbound/i },
      { id: "onepiece", nombre: "One Piece", patron: /one piece/i },
      { id: "magic", nombre: "Magic", patron: /magic: the gathering|\bmtg\b/i },
      { id: "lorcana", nombre: "Lorcana", patron: /lorcana/i }
    ],
    textosACorregir: [["Grantía", "Garantía"]],
    // [ruta rota, ruta correcta]. Hoy el pie enlaza a una página que da 404.
    enlacesRotos: [["/condiciones-generales-de-venta", "/terms"]]
  };
  CONFIG = merge(DEFAULTS, CONFIG);
  var M = CONFIG.modulos;

  /* ------------------------------------------------------------------ */
  /* Utilidades                                                          */
  /* ------------------------------------------------------------------ */
  function merge(a, b) {
    var out = {};
    Object.keys(a).forEach(function (k) { out[k] = a[k]; });
    Object.keys(b || {}).forEach(function (k) {
      out[k] = (a[k] && typeof a[k] === "object" && !Array.isArray(a[k]) && !(a[k] instanceof RegExp))
        ? merge(a[k], b[k]) : b[k];
    });
    return out;
  }
  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
  function el(tag, attrs, html) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (html != null) n.innerHTML = html;
    return n;
  }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function parsePrice(txt) {
    if (!txt) return null;
    var t = String(txt).replace(/[^\d.,]/g, "");
    if (t.indexOf(",") > -1 && t.indexOf(".") > -1) t = t.replace(/\./g, "").replace(",", ".");
    else t = t.replace(",", ".");
    var n = parseFloat(t);
    return isNaN(n) ? null : n;
  }
  var LANG = (document.documentElement.lang || "es").slice(0, 2);
  var IS_ES = LANG === "es";
  function fmt(n) {
    return n.toLocaleString(IS_ES ? "es-ES" : "en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
  }
  function T(es, en) { return IS_ES ? es : en; }
  function store(key, val) {
    try {
      if (val === undefined) return JSON.parse(localStorage.getItem(key) || "null");
      localStorage.setItem(key, JSON.stringify(val));
    } catch (e) { return null; }
  }
  function waLink(msg) { return "https://wa.me/" + CONFIG.whatsapp + "?text=" + encodeURIComponent(msg); }
  function safe(name, fn) { try { fn(); } catch (e) { if (window.console) console.warn("[OnlyCardsBooster] " + name, e); } }

  var MESES = { enero: 0, febrero: 1, marzo: 2, abril: 3, mayo: 4, junio: 5, julio: 6, agosto: 7, septiembre: 8, setiembre: 8, octubre: 9, noviembre: 10, diciembre: 11,
    january: 0, february: 1, march: 2, april: 3, may: 4, june: 5, july: 6, august: 7, september: 8, october: 9, november: 10, december: 11 };

  /** Analiza el nombre de un producto: franquicia, idioma, preventa, nº de sobres. */
  function analyse(name) {
    var info = { franquicia: null, idioma: null, preventa: null, sobres: null };
    CONFIG.franquicias.some(function (f) { if (f.patron.test(name)) { info.franquicia = f; return true; } return false; });
    if (/espa[nñ]ol|castellano/i.test(name) || /\bES\b/.test(name)) info.idioma = "ES";
    else if (/ingl[eé]s|english/i.test(name) || /\bEN\b/.test(name)) info.idioma = "EN";
    else if (/japon[eé]s/i.test(name) || /\bJP\b/.test(name)) info.idioma = "JP";
    var r = name.match(/(?:reserva|preventa|pre-?order)\D{0,12}(\d{1,2})\s+(?:de\s+)?([a-záéíóú]+)/i);
    if (r && MESES[r[2].toLowerCase()] != null) {
      var now = new Date();
      var d = new Date(now.getFullYear(), MESES[r[2].toLowerCase()], parseInt(r[1], 10));
      if (d < new Date(now.getFullYear(), now.getMonth(), now.getDate()) && now.getMonth() - d.getMonth() > 6) d.setFullYear(d.getFullYear() + 1);
      info.preventa = d;
    } else if (/reserva|preventa|pre-?order/i.test(name)) {
      info.preventa = true;
    }
    // Solo productos que son únicamente sobres: en colecciones y álbumes el precio
    // incluye cartas promo, figuras, etc., y el «precio por sobre» engañaría.
    var s = name.match(/(\d+)\s*sobres/i);
    if (s && /caja|bl[ií]ster|display/i.test(name) && !/colecci[oó]n|[aá]lbum|p[oó]ster|figura|entrenador/i.test(name)) info.sobres = parseInt(s[1], 10);
    return info;
  }

  /* ------------------------------------------------------------------ */
  /* Estilos                                                             */
  /* ------------------------------------------------------------------ */
  var CSS = [
    ":root{--ocb-accent:#7b1fa2;--ocb-accent-2:#f5b301;--ocb-ink:#1d1320;--ocb-soft:#f6f0fa;--ocb-ok:#1f8a4c;--ocb-warn:#c0392b}",
    ".ocb-bar{background:var(--ocb-ink);color:#fff;font-size:13px;text-align:center;padding:7px 12px;position:relative;z-index:1031;overflow:hidden;height:33px}",
    ".ocb-bar span{display:block;transition:transform .5s,opacity .5s;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}",
    ".ocb-bar span.ocb-out{transform:translateY(-120%);opacity:0}",
    ".ocb-bar a{color:var(--ocb-accent-2);text-decoration:underline}",
    ".ocb-hero{border-radius:16px;padding:28px 28px 22px;margin:0 0 18px;color:#fff;background:radial-gradient(circle at 85% 20%,rgba(245,179,1,.35),transparent 45%),linear-gradient(135deg,#2a0f3a,#7b1fa2 60%,#b03ad6)}",
    ".ocb-hero h2{font-size:clamp(22px,3vw,32px);font-weight:800;margin:0 0 6px;color:#fff}",
    ".ocb-hero p{margin:0 0 14px;opacity:.9;max-width:620px}",
    ".ocb-hero ul{display:flex;flex-wrap:wrap;gap:8px 18px;list-style:none;padding:0;margin:0;font-size:14px}",
    ".ocb-hero li:before{content:'✓ ';color:var(--ocb-accent-2);font-weight:700}",
    "@media(max-width:575px){.ocb-hero{padding:18px 18px 16px;border-radius:12px}.ocb-hero p{display:none}.ocb-hero ul{display:grid;grid-template-columns:1fr 1fr;gap:4px 10px;font-size:12.5px}.ocb-wa{width:50px;height:50px;right:14px;bottom:14px}}",
    ".ocb-filters{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px;align-items:center}",
    ".ocb-chip{border:1px solid #d9cbe2;background:#fff;border-radius:999px;padding:6px 14px;font-size:14px;cursor:pointer;line-height:1.2;color:var(--ocb-ink)}",
    ".ocb-chip[aria-pressed=true]{background:var(--ocb-accent);border-color:var(--ocb-accent);color:#fff}",
    ".ocb-chip small{opacity:.7;margin-left:4px}",
    ".ocb-sep{width:1px;height:22px;background:#e2d6ea;margin:0 4px}",
    ".ocb-toggle{display:flex;align-items:center;gap:6px;font-size:14px;margin-left:auto;cursor:pointer;user-select:none}",
    ".ocb-hidden{display:none!important}",
    ".ocb-badges{position:absolute;right:8px;bottom:8px;display:flex;gap:4px;z-index:2;flex-wrap:wrap;justify-content:flex-end}",
    ".ocb-badge{font-size:11px;font-weight:700;padding:3px 8px;border-radius:6px;background:rgba(255,255,255,.95);color:var(--ocb-ink);box-shadow:0 1px 3px rgba(0,0,0,.15);letter-spacing:.02em}",
    ".ocb-badge.pre{background:var(--ocb-accent-2);color:#2a1a00}",
    ".ocb-notify{display:inline-flex;align-items:center;gap:6px;font-size:13px;padding:6px 12px;border-radius:8px;background:#e8f7ee;color:#11653a;border:1px solid #bfe6cf;text-decoration:none;margin-top:6px}",
    ".ocb-notify:hover{background:#d6f1e1;color:#0b4f2c}",
    ".ocb-perpack{display:block;font-size:12px;color:#6b5a73;font-weight:500}",
    ".ocb-trust{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;margin:18px 0;padding:14px;border-radius:12px;background:var(--ocb-soft)}",
    ".ocb-trust div{display:flex;gap:8px;align-items:flex-start;font-size:13px;line-height:1.3}",
    ".ocb-trust b{display:block;font-size:13px}",
    ".ocb-trust i{font-style:normal;font-size:18px;line-height:1}",
    ".ocb-count{margin:12px 0;padding:12px 14px;border-radius:12px;background:#fff7dd;border:1px solid #f5d77a;font-size:14px}",
    ".ocb-count strong{font-variant-numeric:tabular-nums;font-size:18px;display:block;margin-top:2px}",
    ".ocb-sticky{position:fixed;left:0;right:0;bottom:0;z-index:1030;background:#fff;box-shadow:0 -4px 16px rgba(0,0,0,.12);padding:10px 16px calc(10px + env(safe-area-inset-bottom));display:flex;align-items:center;gap:12px;transform:translateY(110%);transition:transform .25s}",
    ".ocb-sticky.on{transform:none}",
    ".ocb-sticky .n{flex:1;min-width:0;font-size:13px;line-height:1.25}",
    ".ocb-sticky .n span{display:block;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}",
    ".ocb-sticky .n b{font-size:16px}",
    ".ocb-sticky .btn{white-space:nowrap}",
    "@media(min-width:992px){.ocb-sticky{display:none}}",
    ".ocb-wa{position:fixed;right:18px;bottom:18px;z-index:1029;width:56px;height:56px;border-radius:50%;background:#25d366;display:flex;align-items:center;justify-content:center;box-shadow:0 6px 18px rgba(0,0,0,.25);transition:transform .2s}",
    ".ocb-wa:hover{transform:scale(1.07)}",
    ".ocb-wa svg{width:30px;height:30px;fill:#fff}",
    "body.ocb-has-sticky .ocb-wa{bottom:86px}",
    "@media(min-width:992px){body.ocb-has-sticky .ocb-wa{bottom:18px}}",
    ".ocb-recent{margin:36px 0 12px}",
    ".ocb-recent h3{font-size:18px;font-weight:700;margin:0 0 12px}",
    ".ocb-recent .row{display:flex;gap:12px;overflow-x:auto;padding-bottom:6px;scroll-snap-type:x mandatory}",
    ".ocb-recent a{flex:0 0 150px;scroll-snap-align:start;text-decoration:none;color:inherit;font-size:13px;line-height:1.3}",
    ".ocb-recent img{width:150px;height:150px;object-fit:cover;border-radius:10px;background:#f4f4f4;display:block;margin-bottom:6px}",
    ".ocb-ship{margin:0 0 14px;padding:10px 14px;border-radius:10px;background:var(--ocb-soft);font-size:14px}",
    ".ocb-ship .t{height:6px;border-radius:3px;background:#e5d8ee;margin-top:6px;overflow:hidden}",
    ".ocb-ship .t i{display:block;height:100%;background:var(--ocb-accent);border-radius:3px}"
  ].join("\n");

  /* ------------------------------------------------------------------ */
  /* Módulos                                                             */
  /* ------------------------------------------------------------------ */
  var isProduct = !!$("#product_details");
  var grid = $("#o_wsale_products_grid");
  var isShop = !!grid;
  var isCart = /\/shop\/cart\b/.test(location.pathname);

  function productCards() {
    return $$(".oe_product").map(function (card) {
      var title = $(".o_wsale_products_item_title", card);
      var name = title ? title.textContent.trim() : (($("form", card) || {}).getAttribute && $("form", card).getAttribute("aria-label")) || "";
      var link = $("a.oe_product_image_link", card) || $(".o_wsale_products_item_title a", card);
      var ribbon = $(".o_wsale_ribbon", card);
      var soldOut = (ribbon && /sold out|agotad/i.test(ribbon.textContent)) || !$(".o_wsale_product_btn_primary", card);
      var img = $("img.oe_product_image_img", card);
      var price = parsePrice(($(".product_price .oe_currency_value", card) || {}).textContent);
      return { card: card, name: name, href: link ? link.href : null, soldOut: soldOut, img: img ? img.src : null, price: price, info: analyse(name) };
    });
  }

  // 1. Barra de anuncios rotativa
  function barraAnuncios() {
    var msgs = [
      "🚚 " + CONFIG.envio,
      "✅ " + T("Producto 100% original y sellado de fábrica", "100% original, factory-sealed product"),
      "↩️ " + CONFIG.devolucion,
      CONFIG.recogida ? "📍 " + T("Recogida en tienda: ", "In-store pickup: ") + CONFIG.recogida.calle + ", " + CONFIG.recogida.ciudad + " (" + CONFIG.recogida.textoHorario + ")" : null,
      "💬 " + T("¿Dudas? Escríbenos por ", "Questions? Message us on ") + '<a href="' + waLink(T("Hola Only Cards, tengo una duda", "Hi Only Cards, I have a question")) + '" target="_blank" rel="noopener">WhatsApp</a>'
    ];
    msgs = msgs.filter(Boolean);
    if (CONFIG.envioGratisDesde) msgs.unshift("🎁 " + T("Envío gratis en pedidos desde ", "Free shipping on orders from ") + fmt(CONFIG.envioGratisDesde));
    var bar = el("div", { class: "ocb-bar", role: "region", "aria-label": T("Avisos", "Notices") });
    var span = el("span", null, msgs[0]);
    bar.appendChild(span);
    var header = $("header#top") || document.body.firstElementChild;
    header.parentNode.insertBefore(bar, header);
    var i = 0;
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    setInterval(function () {
      span.classList.add("ocb-out");
      setTimeout(function () { i = (i + 1) % msgs.length; span.innerHTML = msgs[i]; span.classList.remove("ocb-out"); }, 450);
    }, 4500);
  }

  // 2. Cabecera de marca en la tienda (solo en la portada sin búsqueda ni filtros)
  function hero() {
    if (!isShop || location.search.length > 1 || /\/category\//.test(location.pathname)) return;
    var h = el("section", { class: "ocb-hero" },
      "<h2>" + T("Tu tienda de cartas coleccionables", "Your trading card game store") + "</h2>" +
      "<p>" + T("Pokémon, Yu-Gi-Oh! y Riftbound: cajas selladas, colecciones y preventas al mejor precio, con envío rápido desde España.",
        "Pokémon, Yu-Gi-Oh! and Riftbound: sealed boxes, collections and pre-orders, shipped fast from Spain.") + "</p>" +
      "<ul><li>" + T("Producto original sellado", "Original sealed product") + "</li><li>" + esc(CONFIG.envio) + "</li><li>" +
      esc(CONFIG.devolucion) + "</li>" + (CONFIG.recogida ? "<li>" + T("Recogida en tienda en ", "In-store pickup in ") + esc(CONFIG.recogida.ciudad) + "</li>" : "") +
      "<li>" + T("Atención por WhatsApp", "WhatsApp support") + "</li></ul>");
    var anchor = $("#o_wsale_products_header") || grid;
    anchor.parentNode.insertBefore(h, anchor);
  }

  // 3. Filtros por franquicia / idioma / disponibilidad (en cliente)
  function filtros(cards) {
    if (!isShop || cards.length < 4) return;
    var state = store("ocb-filters") || { f: null, l: null, stock: false };
    var counts = {}, langs = {};
    cards.forEach(function (c) {
      var k = c.info.franquicia ? c.info.franquicia.id : "otros";
      counts[k] = (counts[k] || 0) + 1;
      if (c.info.idioma) langs[c.info.idioma] = (langs[c.info.idioma] || 0) + 1;
    });
    var bar = el("div", { class: "ocb-filters", role: "toolbar", "aria-label": T("Filtrar productos", "Filter products") });
    function chip(label, n, group, val) {
      var b = el("button", { type: "button", class: "ocb-chip", "data-g": group, "data-v": val == null ? "" : val, "aria-pressed": "false" },
        esc(label) + (n != null ? "<small>" + n + "</small>" : ""));
      bar.appendChild(b);
      return b;
    }
    chip(T("Todo", "All"), cards.length, "f", null);
    CONFIG.franquicias.forEach(function (f) { if (counts[f.id]) chip(f.nombre, counts[f.id], "f", f.id); });
    if (counts.otros) chip(T("Otros", "Other"), counts.otros, "f", "otros");
    if (Object.keys(langs).length > 1) {
      bar.appendChild(el("span", { class: "ocb-sep", "aria-hidden": "true" }));
      Object.keys(langs).forEach(function (l) { chip({ ES: "🇪🇸 Español", EN: "🇬🇧 English", JP: "🇯🇵 日本語" }[l] || l, langs[l], "l", l); });
    }
    var tg = el("label", { class: "ocb-toggle" }, '<input type="checkbox"> ' + T("Solo disponibles", "In stock only"));
    bar.appendChild(tg);
    var cb = $("input", tg);

    function apply() {
      $$(".ocb-chip", bar).forEach(function (b) {
        var g = b.getAttribute("data-g"), v = b.getAttribute("data-v") || null;
        b.setAttribute("aria-pressed", String(state[g] === v || (g === "f" && v === null && !state.f)));
      });
      cb.checked = !!state.stock;
      cards.forEach(function (c) {
        var fid = c.info.franquicia ? c.info.franquicia.id : "otros";
        var show = (!state.f || state.f === fid) && (!state.l || state.l === c.info.idioma) && (!state.stock || !c.soldOut);
        c.card.classList.toggle("ocb-hidden", !show);
      });
      store("ocb-filters", state);
    }
    bar.addEventListener("click", function (e) {
      var b = e.target.closest(".ocb-chip");
      if (!b) return;
      var g = b.getAttribute("data-g"), v = b.getAttribute("data-v") || null;
      state[g] = (g === "l" && state.l === v) ? null : v;
      apply();
    });
    cb.addEventListener("change", function () { state.stock = cb.checked; apply(); });
    grid.parentNode.insertBefore(bar, grid);
    apply();
  }

  // 4. Insignias (idioma, preventa) y precio por sobre en las tarjetas
  function insignias(cards) {
    cards.forEach(function (c) {
      var imgWrap = $(".oe_product_image", c.card);
      var b = [];
      if (c.info.preventa && M.preventa) {
        b.push('<span class="ocb-badge pre">' + (c.info.preventa instanceof Date
          ? T("Preventa · ", "Pre-order · ") + c.info.preventa.toLocaleDateString(IS_ES ? "es-ES" : "en-GB", { day: "numeric", month: "short" })
          : T("Preventa", "Pre-order")) + "</span>");
      }
      if (c.info.idioma) b.push('<span class="ocb-badge">' + c.info.idioma + "</span>");
      if (b.length && imgWrap) imgWrap.appendChild(el("div", { class: "ocb-badges" }, b.join("")));
      if (M.precioPorSobre && c.info.sobres > 1 && c.price) {
        var p = $(".product_price", c.card);
        if (p) p.appendChild(el("span", { class: "ocb-perpack" }, fmt(c.price / c.info.sobres) + T(" / sobre", " / pack")));
      }
    });
  }

  // 5. Agotado → «Avísame por WhatsApp»
  function avisoAgotado(cards) {
    cards.forEach(function (c) {
      if (!c.soldOut) return;
      var target = $(".o_wsale_product_information", c.card);
      if (!target || $(".ocb-notify", c.card)) return;
      target.appendChild(el("a", { class: "ocb-notify", target: "_blank", rel: "noopener",
        href: waLink(T("Hola, quiero que me aviséis cuando vuelva a estar disponible: ", "Hi, please let me know when this is back in stock: ") + c.name + (c.href ? " — " + c.href : "")) },
        "🔔 " + T("Avísame cuando vuelva", "Notify me")));
    });
  }

  // 6. Ficha de producto: confianza, cuenta atrás, precio por sobre, barra móvil
  function fichaProducto() {
    var details = $("#product_details");
    var nameEl = $("h1", details) || $("[itemprop=name]", details);
    var name = nameEl ? nameEl.textContent.trim() : document.title.split("|")[0].trim();
    var info = analyse(name);
    var priceEl = $(".oe_price .oe_currency_value", details) || $(".product_price .oe_currency_value", details);
    var price = parsePrice(priceEl && priceEl.textContent);
    var addBtn = $("#add_to_cart", details);
    // La plantilla de Odoo contiene textos ocultos de «agotado», así que solo se miran el
    // botón de compra (oculto o desactivado) y la cinta visible sobre la imagen.
    var ribbonSold = $$(".o_wsale_ribbon, .o_ribbons").some(function (r) { return r.offsetParent !== null && /sold out|agotad/i.test(r.textContent); });
    var soldOut = !addBtn || addBtn.classList.contains("disabled") || addBtn.offsetParent === null || ribbonSold;
    var img = $(".o_wsale_product_images img, #o-carousel-product img", document) || $("img.product_detail_img");

    if (M.precioPorSobre && info.sobres > 1 && price) {
      var pc = $(".product_price", details);
      if (pc) pc.parentNode.insertBefore(el("span", { class: "ocb-perpack" }, fmt(price / info.sobres) + T(" por sobre · ", " per pack · ") + info.sobres + T(" sobres", " packs")), pc.nextSibling);
    }

    if (M.preventa && info.preventa instanceof Date) {
      var box = el("div", { class: "ocb-count" });
      var target = new Date(info.preventa.getTime());
      var tick = function () {
        var ms = target - new Date();
        if (ms <= 0) { box.innerHTML = "🎉 " + T("¡Ya disponible! Los pedidos de preventa se envían por orden de reserva.", "Out now! Pre-orders ship in order of reservation."); return false; }
        var d = Math.floor(ms / 864e5), h = Math.floor(ms / 36e5) % 24, m = Math.floor(ms / 6e4) % 60, s = Math.floor(ms / 1e3) % 60;
        box.innerHTML = "⏳ " + T("Preventa: lanzamiento el ", "Pre-order: releases on ") +
          target.toLocaleDateString(IS_ES ? "es-ES" : "en-GB", { day: "numeric", month: "long" }) +
          "<strong>" + d + "d " + h + "h " + String(m).padStart(2, "0") + "m " + String(s).padStart(2, "0") + "s</strong>" +
          T("Reserva ahora y asegura tu unidad.", "Reserve now to secure your copy.");
        return true;
      };
      if (tick()) { var iv = setInterval(function () { if (!tick()) clearInterval(iv); }, 1000); }
      var pp = $(".product_price", details);
      (pp && pp.parentNode ? pp.parentNode : details).insertBefore(box, pp ? pp.nextSibling : null);
    }

    if (M.confianzaProducto) {
      var trust = el("div", { class: "ocb-trust" },
        "<div><i>✅</i><span><b>" + T("100% original", "100% original") + "</b>" + T("Sellado de fábrica", "Factory sealed") + "</span></div>" +
        "<div><i>🚚</i><span><b>" + T("Envío rápido", "Fast shipping") + "</b>" + esc(CONFIG.envio) + "</span></div>" +
        "<div><i>↩️</i><span><b>" + T("Devolución fácil", "Easy returns") + "</b>" + esc(CONFIG.devolucion) + "</span></div>" +
        (CONFIG.recogida ? "<div><i>📍</i><span><b>" + T("Recógelo en ", "Pick up in ") + esc(CONFIG.recogida.ciudad) + "</b>" + esc(CONFIG.recogida.calle) + "</span></div>" : "") +
        "<div><i>💬</i><span><b>" + T("Atención directa", "Direct support") + '</b><a href="' + waLink(T("Hola, tengo una pregunta sobre: ", "Hi, I have a question about: ") + name + " — " + location.href) + '" target="_blank" rel="noopener">WhatsApp</a></span></div>');
      var anchor = addBtn ? addBtn.closest("#o_wsale_cta_wrapper, .o_wsale_product_details_content_section_cta, .js_main_product") || addBtn.parentNode : null;
      if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(trust, anchor.nextSibling);
      else details.appendChild(trust);
    }

    if (M.avisoAgotado && soldOut) {
      var n = el("a", { class: "ocb-notify", target: "_blank", rel: "noopener",
        href: waLink(T("Hola, quiero que me aviséis cuando vuelva a estar disponible: ", "Hi, please let me know when this is back in stock: ") + name + " — " + location.href) },
        "🔔 " + T("Avísame por WhatsApp cuando vuelva", "Notify me on WhatsApp when it's back"));
      var tr = $(".ocb-trust");
      if (tr && tr.parentNode) tr.parentNode.insertBefore(n, tr); else details.appendChild(n);
    }

    if (M.barraMovilCompra && addBtn && !soldOut) {
      var bar = el("div", { class: "ocb-sticky", "aria-hidden": "true" },
        '<div class="n"><span>' + esc(name) + "</span><b>" + (price != null ? fmt(price) : "") + "</b></div>" +
        '<button type="button" class="btn btn-primary">' + T("Añadir a la cesta", "Add to cart") + "</button>");
      document.body.appendChild(bar);
      document.body.classList.add("ocb-has-sticky");
      // Odoo vuelve a pintar el bloque de compra tras cargar: se busca el botón cada vez.
      $("button", bar).addEventListener("click", function () { var b = $("#add_to_cart"); if (b) b.click(); });
      var pending = false;
      var update = function () {
        pending = false;
        var b = $("#add_to_cart");
        var on = !!b && b.getBoundingClientRect().bottom < 0;
        bar.classList.toggle("on", on);
        bar.setAttribute("aria-hidden", String(!on));
      };
      window.addEventListener("scroll", function () { if (!pending) { pending = true; requestAnimationFrame(update); } }, { passive: true });
      update();
    }

    if (M.vistosRecientemente) {
      var list = (store("ocb-recent") || []).filter(function (p) { return p.href !== location.href.split("?")[0]; });
      list.unshift({ name: name, href: location.href.split("?")[0], img: img ? img.src : null, price: price });
      store("ocb-recent", list.slice(0, 12));
    }

    if (M.seo) seoProducto(name, price, soldOut, img, info);
  }

  // 7. Vistos recientemente
  function vistosRecientemente() {
    var list = (store("ocb-recent") || []).filter(function (p) { return p.href !== location.href.split("?")[0]; }).slice(0, 8);
    if (list.length < 2) return;
    var sec = el("section", { class: "ocb-recent container" }, "<h3>" + T("Vistos recientemente", "Recently viewed") + '</h3><div class="row"></div>');
    var row = $(".row", sec);
    list.forEach(function (p) {
      row.appendChild(el("a", { href: p.href },
        (p.img ? '<img loading="lazy" alt="" src="' + esc(p.img) + '">' : "") + esc(p.name) + (p.price != null ? "<br><b>" + fmt(p.price) + "</b>" : "")));
    });
    var main = $("#wrap") || $("main");
    if (main) main.appendChild(sec);
  }

  // 8. Botón flotante de WhatsApp
  function whatsappFlotante() {
    var msg = isProduct ? T("Hola, tengo una pregunta sobre: ", "Hi, I have a question about: ") + document.title.split("|")[0].trim() + " — " + location.href
      : T("Hola Only Cards, tengo una consulta", "Hi Only Cards, I have a question");
    var a = el("a", { class: "ocb-wa", href: waLink(msg), target: "_blank", rel: "noopener", "aria-label": T("Escríbenos por WhatsApp", "Message us on WhatsApp") },
      '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M16 3C8.8 3 3 8.7 3 15.8c0 2.5.7 4.9 2 7L3 29l6.4-2c2 1.1 4.3 1.7 6.6 1.7 7.2 0 13-5.7 13-12.8S23.2 3 16 3zm0 23.4c-2.1 0-4.1-.6-5.9-1.7l-.4-.3-3.8 1.2 1.2-3.7-.3-.4c-1.2-1.8-1.8-3.8-1.8-5.9C5 9.9 9.9 5.1 16 5.1s11 4.8 11 10.7-4.9 10.6-11 10.6zm6-7.9c-.3-.2-1.9-1-2.2-1.1-.3-.1-.5-.2-.7.2-.2.3-.8 1-1 1.2-.2.2-.4.2-.7.1-.3-.2-1.4-.5-2.6-1.6-1-.9-1.6-1.9-1.8-2.3-.2-.3 0-.5.1-.7l.5-.6c.2-.2.2-.3.3-.6.1-.2 0-.4 0-.6l-1-2.4c-.3-.6-.5-.5-.7-.5h-.6c-.2 0-.6.1-.9.4-.3.3-1.2 1.1-1.2 2.7s1.2 3.2 1.4 3.4c.2.2 2.4 3.6 5.8 5 .8.3 1.4.5 1.9.7.8.3 1.5.2 2.1.1.6-.1 1.9-.8 2.2-1.5.3-.7.3-1.4.2-1.5-.1-.2-.3-.3-.6-.4z"/></svg>');
    document.body.appendChild(a);
  }

  // 9. SEO: datos estructurados (Google los lee aunque se inyecten por JS) y meta description
  function addJsonLd(obj) {
    var s = document.createElement("script");
    s.type = "application/ld+json";
    s.textContent = JSON.stringify(obj);
    document.head.appendChild(s);
  }
  function ensureMetaDescription(text) {
    if ($('meta[name="description"]')) return;
    var m = el("meta", { name: "description", content: text.slice(0, 158) });
    document.head.appendChild(m);
  }
  function seoProducto(name, price, soldOut, img, info) {
    var desc = $(".o_wsale_product_details_content_section_title .oe_structure, #product_full_description, [itemprop=description]");
    var dtext = desc ? (desc.innerText || desc.textContent).replace(/\s+/g, " ").trim() : "";
    if (dtext.length < 40) dtext = ""; // producto sin descripción: se usa el texto genérico
    var offer = {
      "@type": "Offer", url: location.href.split("?")[0], priceCurrency: "EUR",
      availability: soldOut ? "https://schema.org/OutOfStock" : (info.preventa ? "https://schema.org/PreOrder" : "https://schema.org/InStock"),
      itemCondition: "https://schema.org/NewCondition",
      seller: { "@type": "Organization", name: "Only Cards" }
    };
    if (price != null) offer.price = price.toFixed(2);
    if (info.preventa instanceof Date) offer.availabilityStarts = info.preventa.toISOString().slice(0, 10);
    // Odoo 18 ya publica un Product básico: si existe, se enriquece en lugar de duplicarlo.
    var existing = null, existingScript = null, existingData = null;
    $$('script[type="application/ld+json"]').some(function (s) {
      try {
        var data = JSON.parse(s.textContent);
        var arr = Array.isArray(data) ? data : [data];
        for (var i = 0; i < arr.length; i++) if (arr[i]["@type"] === "Product") { existing = arr[i]; existingScript = s; existingData = data; return true; }
      } catch (e) { /* JSON-LD ajeno inválido: se ignora */ }
      return false;
    });
    var prod = existing || { "@context": "https://schema.org", "@type": "Product", name: name };
    if (existing && existing.offers) {
      var o = Array.isArray(existing.offers) ? existing.offers[0] : existing.offers;
      Object.keys(offer).forEach(function (k) { if (k !== "price" || o.price == null) o[k] = offer[k]; });
    } else prod.offers = offer;
    if (img && !prod.image) prod.image = [img.src];
    if (dtext) prod.description = dtext.slice(0, 500);
    if (info.franquicia) prod.brand = { "@type": "Brand", name: info.franquicia.nombre };
    if (info.idioma) prod.inLanguage = { ES: "es", EN: "en", JP: "ja" }[info.idioma];
    prod.sku = prod.sku || (location.pathname.match(/-(\d+)$/) || [])[1];
    if (existingScript) existingScript.textContent = JSON.stringify(existingData);
    else addJsonLd(prod);
    addJsonLd({
      "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: [
        { "@type": "ListItem", position: 1, name: T("Tienda", "Shop"), item: location.origin + "/" + (IS_ES ? "es/" : "") + "shop" },
        { "@type": "ListItem", position: 2, name: name, item: location.href.split("?")[0] }
      ]
    });
    ensureMetaDescription(dtext || (name + " — " + T("compra en Only Cards. Producto original sellado. ", "buy at Only Cards. Original sealed product. ") + CONFIG.envio + "."));
  }
  function seoGlobal(cards) {
    addJsonLd({
      "@context": "https://schema.org", "@type": "Store", name: "Only Cards", url: location.origin,
      telephone: "+" + CONFIG.whatsapp, email: CONFIG.email,
      logo: location.origin + "/logo.png?company=1", image: location.origin + "/web/image/website/1/social_default_image",
      priceRange: "€€", currenciesAccepted: "EUR",
      address: CONFIG.recogida ? { "@type": "PostalAddress", streetAddress: CONFIG.recogida.calle, addressLocality: CONFIG.recogida.ciudad,
        postalCode: CONFIG.recogida.cp, addressRegion: CONFIG.recogida.provincia, addressCountry: CONFIG.recogida.pais } : undefined,
      geo: CONFIG.recogida ? { "@type": "GeoCoordinates", latitude: CONFIG.recogida.lat, longitude: CONFIG.recogida.lng } : undefined,
      openingHoursSpecification: CONFIG.recogida ? CONFIG.recogida.horario.map(function (h) {
        return { "@type": "OpeningHoursSpecification", dayOfWeek: "https://schema.org/" + h[0], opens: h[1], closes: h[2] };
      }) : undefined,
      sameAs: CONFIG.instagram && CONFIG.instagram !== "https://www.instagram.com/" ? [CONFIG.instagram] : undefined
    });
    if (isShop && cards.length) {
      addJsonLd({
        "@context": "https://schema.org", "@type": "ItemList",
        itemListElement: cards.filter(function (c) { return c.href; }).map(function (c, i) { return { "@type": "ListItem", position: i + 1, url: c.href, name: c.name }; })
      });
      ensureMetaDescription(T("Only Cards: tienda online de cartas coleccionables. Cajas selladas, preventas y colecciones de Pokémon, Yu-Gi-Oh! y Riftbound. ",
        "Only Cards: online trading card store. Sealed boxes, pre-orders and collections of Pokémon, Yu-Gi-Oh! and Riftbound. ") + CONFIG.envio + ".");
    }
  }

  // 10. Correcciones de texto (erratas visibles en la plantilla)
  function corregirTextos() {
    var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null);
    var n;
    while ((n = w.nextNode())) {
      CONFIG.textosACorregir.forEach(function (p) { if (n.nodeValue.indexOf(p[0]) > -1) n.nodeValue = n.nodeValue.split(p[0]).join(p[1]); });
    }
    // Enlaces rotos: se compara la ruta sin el prefijo de idioma (/en, /es…).
    $$("a[href]").forEach(function (a) {
      if (a.origin !== location.origin) return;
      var m = a.pathname.match(/^(\/[a-z]{2}(?:_[A-Z]{2})?)?(\/.*)$/);
      if (!m) return;
      CONFIG.enlacesRotos.forEach(function (r) { if (m[2] === r[0]) a.setAttribute("href", (m[1] || "") + r[1]); });
    });
  }

  // 11. Barra de envío gratis en el carrito (solo si hay umbral definido)
  function barraEnvioGratis() {
    if (!CONFIG.envioGratisDesde || !isCart) return;
    var totalEl = $("#order_total .oe_currency_value, tr#order_total .oe_currency_value, [data-oe-expression*=amount_total] .oe_currency_value");
    var total = parsePrice(totalEl && totalEl.textContent);
    if (total == null) return;
    var falta = CONFIG.envioGratisDesde - total;
    var pct = Math.max(0, Math.min(100, (total / CONFIG.envioGratisDesde) * 100));
    var box = el("div", { class: "ocb-ship" }, (falta > 0
      ? T("Te faltan <b>", "Only <b>") + fmt(falta) + T("</b> para el envío gratis 🎁", "</b> away from free shipping 🎁")
      : "🎉 " + T("¡Tienes envío gratis!", "You've unlocked free shipping!")) + '<div class="t"><i style="width:' + pct + '%"></i></div>');
    var wrap = $(".oe_cart") || $("#wrap .container");
    if (wrap) wrap.insertBefore(box, wrap.firstChild);
  }

  /* ------------------------------------------------------------------ */
  /* Arranque                                                            */
  /* ------------------------------------------------------------------ */
  function init() {
    if (window.__ocbLoaded) return;
    window.__ocbLoaded = true;
    // No tocar el editor de Odoo.
    if (document.body.classList.contains("editor_enable") || /[?&]enable_editor=/.test(location.search)) return;
    document.head.appendChild(el("style", { id: "ocb-css" }, CSS));
    var cards = isShop ? productCards() : [];
    if (M.corregirTextos) safe("textos", corregirTextos);
    if (M.barraAnuncios) safe("barra", barraAnuncios);
    if (M.hero) safe("hero", hero);
    if (M.filtrosFranquicia) safe("filtros", function () { filtros(cards); });
    if (M.insignias) safe("insignias", function () { insignias(cards); });
    if (M.avisoAgotado) safe("agotado", function () { avisoAgotado(cards); });
    if (isProduct) safe("ficha", fichaProducto);
    if (M.vistosRecientemente && (isShop || isProduct)) safe("recientes", vistosRecientemente);
    if (M.whatsappFlotante) safe("whatsapp", whatsappFlotante);
    if (M.seo) safe("seo", function () { seoGlobal(cards); });
    if (M.barraEnvioGratis) safe("envio", barraEnvioGratis);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
