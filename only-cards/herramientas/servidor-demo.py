"""Vista previa navegable de only-cards.com con las mejoras aplicadas.

Hace de intermediario con la web real: cada página se pide a www.only-cards.com,
se le inyecta el Booster y las fotos de producto se sustituyen por las
re-encuadradas de only-cards/imagenes/mejoradas. No modifica nada en la tienda
real; el carrito y el inicio de sesión funcionan contra ella como siempre.

Uso:
    python3 only-cards/herramientas/servidor-demo.py [puerto]     # por defecto 8080

Opciones por variable de entorno:
    DEMO_SIN_BOOSTER=1   no inyectar el script (para comparar)
    DEMO_SIN_IMAGENES=1  servir las fotos originales
"""
from __future__ import annotations

import os
import re
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ORIGEN = "https://www.only-cards.com"
RAIZ = Path(__file__).resolve().parent.parent
BOOSTER = RAIZ / "booster" / "only-cards-booster.js"
IMAGENES = RAIZ / "imagenes" / "mejoradas"
# Configuración de demostración: el umbral real de envío gratis lo decide el dueño.
CONFIG_DEMO = "window.ONLY_CARDS_BOOSTER_CONFIG = { envioGratisDesde: 100 };"

SIN_BOOSTER = os.environ.get("DEMO_SIN_BOOSTER") == "1"
SIN_IMAGENES = os.environ.get("DEMO_SIN_IMAGENES") == "1"

RE_IMAGEN = re.compile(r"^/web/image/product\.(?:product|template)/(\d+)/image_\d+")
CABECERAS_FUERA = {"content-encoding", "content-length", "transfer-encoding", "connection",
                   "content-security-policy", "strict-transport-security", "alt-svc", "keep-alive"}


class SinRedirecciones(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # las redirecciones las ve el navegador
        return None


abridor = urllib.request.build_opener(SinRedirecciones)


def imagenes_por_id() -> dict[str, Path]:
    if SIN_IMAGENES or not IMAGENES.is_dir():
        return {}
    out = {}
    for f in IMAGENES.glob("*.jpg"):
        m = re.search(r"-(\d+)\.jpg$", f.name)
        if m:
            out[m.group(1)] = f
    return out


class Demo(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    imagenes = imagenes_por_id()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.command, self.path))

    def do_GET(self):
        self.reenviar()

    def do_HEAD(self):
        self.reenviar()

    def do_POST(self):
        self.reenviar()

    def responder(self, estado: int, cabeceras: list[tuple[str, str]], cuerpo: bytes):
        self.send_response(estado)
        for k, v in cabeceras:
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(cuerpo)

    def reenviar(self):
        m = RE_IMAGEN.match(self.path)
        if m and m.group(1) in self.imagenes and self.command in ("GET", "HEAD"):
            self.responder(200, [("Content-Type", "image/jpeg"), ("Cache-Control", "no-cache")],
                           self.imagenes[m.group(1)].read_bytes())
            return

        cuerpo = None
        if self.command == "POST":
            cuerpo = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        cab = {k: v for k, v in self.headers.items()
               if k.lower() not in ("host", "accept-encoding", "connection", "origin", "referer")}
        cab["Accept-Encoding"] = "identity"
        cab["Origin"] = ORIGEN
        cab["Referer"] = ORIGEN + "/"
        req = urllib.request.Request(ORIGEN + self.path, data=cuerpo, headers=cab, method=self.command)
        try:
            resp = abridor.open(req, timeout=40)
        except urllib.error.HTTPError as e:
            resp = e
        except urllib.error.URLError as e:
            self.responder(502, [("Content-Type", "text/plain; charset=utf-8")],
                           f"No se pudo contactar con {ORIGEN}: {e.reason}".encode())
            return

        datos = resp.read()
        cabeceras = []
        tipo = ""
        for k, v in resp.headers.items():
            kl = k.lower()
            if kl in CABECERAS_FUERA:
                continue
            if kl == "content-type":
                tipo = v
            if kl == "location":
                v = v.replace(ORIGEN, "").replace("https://only-cards.com", "") or "/"
            if kl == "set-cookie":
                # La demo va por http://localhost: quitar Secure/Domain/SameSite=None.
                v = re.sub(r";\s*(Secure|Domain=[^;]*|SameSite=None)", "", v, flags=re.I)
            cabeceras.append((k, v))

        if "text/html" in tipo:
            html = datos.decode("utf-8", "replace")
            html = html.replace(ORIGEN, "").replace("https://only-cards.com", "")
            if not SIN_BOOSTER and "</body>" in html:
                extra = ("<script>" + CONFIG_DEMO + "</script>\n<script>" +
                         BOOSTER.read_text(encoding="utf-8").replace("</script", "<\\/script") + "</script>\n")
                html = html.replace("</body>", extra + "</body>", 1)
            datos = html.encode("utf-8")
            cabeceras.append(("Cache-Control", "no-store"))
        self.responder(resp.status, cabeceras, datos)


def main() -> int:
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    srv = ThreadingHTTPServer(("0.0.0.0", puerto), Demo)
    print(f"Demo de Only Cards en http://localhost:{puerto}/es/shop  "
          f"(booster: {'no' if SIN_BOOSTER else 'sí'}, fotos nuevas: {len(Demo.imagenes)})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
