// Abre la web real de Only Cards, inyecta el booster y guarda capturas antes/después.
// Uso: node only-cards/herramientas/vista-previa.js [carpeta-salida]
// Requiere Playwright (require('playwright')) y acceso de red a www.only-cards.com.
const path = require("path");
const fs = require("fs");
const { chromium, devices } = require("playwright");

const BASE = "https://www.only-cards.com/es";
const BOOSTER = path.join(__dirname, "..", "booster", "only-cards-booster.js");
const OUT = process.argv[2] || path.join(__dirname, "..", "capturas");
// Solo para la demo: el umbral de envío gratis real lo decide el dueño.
const DEMO_CONFIG = "window.ONLY_CARDS_BOOSTER_CONFIG = { envioGratisDesde: 100 };";

const PAGES = [
  { id: "tienda", url: `${BASE}/shop` },
  { id: "producto", url: `${BASE}/shop/dominio-delta-caja-sellada-36-sobres-espanol-25` },
  { id: "preventa", url: `${BASE}/shop/magnificent-maestros-tuckbox-en-reserva-12-noviembre-19` },
  { id: "agotado", url: `${BASE}/shop/coleccion-premium-ditto-30-aniversario-pokemon-espanol-22` },
];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const launch = process.env.HTTPS_PROXY ? { proxy: { server: process.env.HTTPS_PROXY } } : {};
  const browser = await chromium.launch(launch);
  const code = fs.readFileSync(BOOSTER, "utf8");
  const report = [];

  for (const [vista, ctxOpts] of [
    ["escritorio", { viewport: { width: 1366, height: 900 }, deviceScaleFactor: 1, locale: "es-ES" }],
    ["movil", { ...devices["iPhone 13"], locale: "es-ES" }],
  ]) {
    const ctx = await browser.newContext(ctxOpts);
    for (const p of PAGES) {
      const page = await ctx.newPage();
      const errors = [];
      page.on("console", (m) => { if (m.type() === "warning" && m.text().includes("OnlyCardsBooster")) errors.push(m.text()); });
      page.on("pageerror", (e) => errors.push(String(e)));
      await page.goto(p.url, { waitUntil: "networkidle" });
      // Aceptar solo cookies necesarias para que el banner no tape la captura.
      await page.locator("#cookies-consent-essential, .js_close_popup, a:has-text('Solo las necesarias')").first().click({ timeout: 2000 }).catch(() => {});
      await page.screenshot({ path: path.join(OUT, `${p.id}-${vista}-antes.jpg`), type: "jpeg", quality: 80 });
      await page.addScriptTag({ content: DEMO_CONFIG });
      await page.addScriptTag({ content: code });
      await page.waitForTimeout(600);
      if (p.id !== "tienda") await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: path.join(OUT, `${p.id}-${vista}-despues.jpg`), type: "jpeg", quality: 80 });
      if (p.id === "producto" && vista === "movil") {
        await page.evaluate(() => {
          const b = document.querySelector("#add_to_cart");
          window.scrollTo(0, b.getBoundingClientRect().bottom + window.scrollY + 300);
        });
        await page.waitForTimeout(500);
        await page.screenshot({ path: path.join(OUT, `${p.id}-${vista}-despues-scroll.jpg`), type: "jpeg", quality: 80 });
      }
      const ld = await page.evaluate(() =>
        Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map((s) => JSON.parse(s.textContent)["@type"]));
      const meta = await page.evaluate(() => (document.querySelector('meta[name="description"]') || {}).content || null);
      const rotos = await page.evaluate(() => document.querySelectorAll('a[href*="condiciones-generales-de-venta"]').length);
      if (rotos) errors.push(`${rotos} enlace(s) a la página 404 de condiciones`);
      report.push({ vista, pagina: p.id, jsonld: ld, metaDescription: meta, errores: errors });
      await page.close();
    }
    // Tienda con las fotos re-encuadradas (only-cards/imagenes/mejoradas), servidas en lugar de las de Odoo.
    const IMGS = path.join(__dirname, "..", "imagenes", "mejoradas");
    if (fs.existsSync(IMGS)) {
      const porId = {};
      for (const f of fs.readdirSync(IMGS)) { const m = f.match(/-(\d+)\.jpg$/); if (m) porId[m[1]] = path.join(IMGS, f); }
      const page = await ctx.newPage();
      await page.route(/\/web\/image\/product\.(product|template)\/(\d+)\/image_/, (route) => {
        const id = route.request().url().match(/product\.(?:product|template)\/(\d+)\//)[1];
        return porId[id] ? route.fulfill({ path: porId[id], contentType: "image/jpeg" }) : route.continue();
      });
      await page.goto(`${BASE}/shop`, { waitUntil: "networkidle" });
      await page.locator("#cookies-consent-essential, .js_close_popup, a:has-text('Solo las necesarias')").first().click({ timeout: 2000 }).catch(() => {});
      await page.addScriptTag({ content: DEMO_CONFIG });
      await page.addScriptTag({ content: code });
      await page.waitForTimeout(600);
      await page.evaluate(() => {
        const g = document.querySelector(".ocb-filters") || document.querySelector("#o_wsale_products_grid");
        window.scrollTo(0, g.getBoundingClientRect().top + window.scrollY - 80);
      });
      await page.waitForTimeout(400);
      await page.screenshot({ path: path.join(OUT, `tienda-${vista}-despues-imagenes.jpg`), type: "jpeg", quality: 80 });
      // Misma posición sin las fotos nuevas, para comparar.
      await page.unrouteAll();
      await page.reload({ waitUntil: "networkidle" });
      await page.addScriptTag({ content: DEMO_CONFIG });
      await page.addScriptTag({ content: code });
      await page.waitForTimeout(600);
      await page.evaluate(() => {
        const g = document.querySelector(".ocb-filters") || document.querySelector("#o_wsale_products_grid");
        window.scrollTo(0, g.getBoundingClientRect().top + window.scrollY - 80);
      });
      await page.waitForTimeout(400);
      await page.screenshot({ path: path.join(OUT, `tienda-${vista}-despues-imagenes-antes.jpg`), type: "jpeg", quality: 80 });
      await page.close();
    }
    await ctx.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(OUT, "informe.json"), JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  if (report.some((r) => r.errores.length)) process.exit(1);
})().catch((e) => { console.error(e); process.exit(1); });
