"""Exporta la web mejorada como archivos HTML que se abren sin servidor.

Descarga varias páginas de only-cards.com, incrusta las fotos re-encuadradas,
quita el JavaScript de Odoo (que sin servidor no funciona) e incluye el
Booster, que se ejecuta al abrir el archivo: filtros, cuenta atrás, barra
móvil, etc. Los estilos y tipografías se cargan desde la web real, así que
hace falta conexión a internet para verlos bien.

Uso:
    python3 only-cards/herramientas/exportar-demo.py [carpeta-salida]   # por defecto only-cards/demo
"""
from __future__ import annotations

import base64
import io
import re
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ORIGEN = "https://www.only-cards.com"
RAIZ = Path(__file__).resolve().parent.parent
BOOSTER = RAIZ / "booster" / "only-cards-booster.js"
IMAGENES = RAIZ / "imagenes" / "mejoradas"
CONFIG_DEMO = "window.ONLY_CARDS_BOOSTER_CONFIG = { envioGratisDesde: 100 };"

PAGINAS = {
    "/shop": "index.html",
    "/shop/dominio-delta-caja-sellada-36-sobres-espanol-25": "producto-dominio-delta.html",
    "/shop/magnificent-maestros-tuckbox-en-reserva-12-noviembre-19": "producto-preventa.html",
    "/shop/coleccion-premium-ditto-30-aniversario-pokemon-espanol-22": "producto-agotado.html",
}


def descargar(ruta: str) -> str:
    req = urllib.request.Request(ORIGEN + ruta, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "es-ES"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def imagenes_data_uri() -> dict[str, str]:
    out = {}
    for f in IMAGENES.glob("*.jpg"):
        m = re.search(r"-(\d+)\.jpg$", f.name)
        if not m:
            continue
        im = Image.open(f)
        im.thumbnail((700, 700), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=82, optimize=True)
        out[m.group(1)] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return out


def procesar(html: str, imgs: dict[str, str]) -> str:
    # Fuera el JavaScript de Odoo; se conservan los datos estructurados (ld+json).
    html = re.sub(r"(?is)<script(?![^>]*application/ld\+json)[^>]*>.*?</script>", "", html)
    html = re.sub(r"(?is)<script(?![^>]*application/ld\+json)[^>]*/>", "", html)
    # Fotos de producto re-encuadradas, incrustadas.
    def foto(m):
        return imgs.get(m.group(2), m.group(0))
    html = re.sub(r'(/web/image/product\.(?:product|template)/(\d+)/image_\d+[^"\'\s)]*)', foto, html)
    # Enlaces entre las páginas exportadas; el resto apunta a la web real.
    for ruta, archivo in PAGINAS.items():
        for pref in ("/es", "/en", ""):
            html = html.replace(f'href="{pref}{ruta}"', f'href="{archivo}"')
    html = re.sub(r'(href|src|srcset|action)="/(?!/)', rf'\1="{ORIGEN}/', html)
    html = re.sub(r"url\((['\"]?)/(?!/)", rf"url(\1{ORIGEN}/", html)
    # Banner de cookies: sin JS no se puede cerrar.
    html = re.sub(r'(?is)<div[^>]*id="website_cookies_bar".*?</div>\s*</div>\s*</div>', "", html)
    aviso = ('<div style="background:#fff7dd;color:#4a3a00;font:13px system-ui,sans-serif;text-align:center;padding:6px 12px">'
             "Demostración de las mejoras propuestas para only-cards.com · no es la tienda real · "
             "el carrito y la compra no funcionan aquí</div>")
    html = re.sub(r"(<body[^>]*>)", r"\1" + aviso, html, count=1)
    booster = BOOSTER.read_text(encoding="utf-8").replace("</script", "<\\/script")
    extra = f"<script>{CONFIG_DEMO}</script>\n<script>{booster}</script>\n"
    return html.replace("</body>", extra + "</body>", 1)


def main() -> int:
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "demo"
    salida.mkdir(parents=True, exist_ok=True)
    imgs = imagenes_data_uri()
    for ruta, archivo in PAGINAS.items():
        destino = salida / archivo
        destino.write_text(procesar(descargar(ruta), imgs), encoding="utf-8")
        print(f"{destino}  ({destino.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
