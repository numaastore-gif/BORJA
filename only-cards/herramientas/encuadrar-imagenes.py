"""Descarga las fotos de producto de only-cards.com y las re-encuadra.

Cada imagen se recorta al producto (quitando márgenes y fondos lisos), se centra
en un lienzo cuadrado blanco con el mismo margen para todas y se le añade una
sombra de apoyo suave. Así el listado de Odoo, que recorta en «cover», deja de
cortar productos y todas las fichas se ven del mismo tamaño.

Uso:
    python3 only-cards/herramientas/encuadrar-imagenes.py [carpeta-salida]

Genera <salida>/originales/, <salida>/mejoradas/ y <salida>/comparativa.jpg.
Requiere Pillow y numpy, y acceso de red a www.only-cards.com.
"""
from __future__ import annotations

import html
import io
import re
import sys
import urllib.request
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = "https://www.only-cards.com"
LADO = 1200            # lienzo final (px)
OCUPACION = 0.84       # fracción del lado que ocupa el producto
TOLERANCIA = 22        # diferencia máxima con el color de fondo (0-255)
FONDO = (255, 255, 255)


def descargar(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (OnlyCards image tool)"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def productos() -> list[tuple[int, str, str]]:
    """(id, slug, nombre) de los productos publicados en la tienda."""
    page = descargar(f"{BASE}/es/shop?ppg=200").decode("utf-8")
    out, vistos = [], set()
    for m in re.finditer(r'href="/(?:es/|en/)?shop/([^"?#]+-(\d+))" class="oe_product_image_link[^"]*" title="([^"]*)"', page):
        slug, pid, nombre = m.group(1), int(m.group(2)), html.unescape(m.group(3))
        if pid not in vistos:
            vistos.add(pid)
            out.append((pid, slug, nombre))
    return out


def a_rgb(im: Image.Image) -> tuple[Image.Image, np.ndarray | None]:
    """Devuelve la imagen sobre blanco y, si tenía transparencia, su máscara."""
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        alfa = np.asarray(im.getchannel("A"))
        if alfa.min() < 250:
            fondo = Image.new("RGBA", im.size, FONDO + (255,))
            fondo.alpha_composite(im)
            return fondo.convert("RGB"), alfa > 16
    return im.convert("RGB"), None


def mascara_fondo(px: np.ndarray) -> np.ndarray | None:
    """Píxeles de fondo conectados con el borde, si el borde es un color liso.

    Devuelve None cuando la foto llega hasta el borde (no hay fondo que quitar).
    """
    h, w, _ = px.shape
    borde = np.concatenate([px[0], px[-1], px[:, 0], px[:, -1]]).astype(int)
    color = np.median(borde, axis=0)
    cerca = np.abs(borde - color).max(axis=1) <= TOLERANCIA
    if cerca.mean() < 0.85:          # el borde no es uniforme: es parte del producto
        return None
    parecido = np.abs(px.astype(int) - color).max(axis=2) <= TOLERANCIA
    # Relleno por inundación desde el borde: solo es fondo lo conectado con él,
    # para no borrar zonas blancas dentro del producto.
    fondo = np.zeros((h, w), bool)
    cola = deque()
    for x in range(w):
        for y in (0, h - 1):
            if parecido[y, x] and not fondo[y, x]:
                fondo[y, x] = True
                cola.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if parecido[y, x] and not fondo[y, x]:
                fondo[y, x] = True
                cola.append((y, x))
    while cola:
        y, x = cola.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and parecido[ny, nx] and not fondo[ny, nx]:
                fondo[ny, nx] = True
                cola.append((ny, nx))
    return fondo


def caja(producto: np.ndarray) -> tuple[int, int, int, int]:
    """Caja del producto ignorando motas sueltas (filas/columnas casi vacías)."""
    h, w = producto.shape
    filas = np.where(producto.sum(axis=1) > max(2, w * 0.004))[0]
    cols = np.where(producto.sum(axis=0) > max(2, h * 0.004))[0]
    if len(filas) == 0 or len(cols) == 0:
        return 0, 0, w, h
    return cols[0], filas[0], cols[-1] + 1, filas[-1] + 1


def encuadrar(datos: bytes) -> Image.Image:
    im, alfa = a_rgb(Image.open(io.BytesIO(datos)))
    px = np.asarray(im)
    if alfa is not None:
        producto = alfa
    else:
        fondo = mascara_fondo(px)
        producto = ~fondo if fondo is not None else np.ones(px.shape[:2], bool)
    x0, y0, x1, y1 = caja(producto)
    recorte = im.crop((x0, y0, x1, y1))
    mascara = Image.fromarray((producto[y0:y1, x0:x1] * 255).astype(np.uint8))
    # El fondo original se sustituye por blanco con un borde suavizado.
    mascara = mascara.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))

    escala = (LADO * OCUPACION) / max(recorte.size)
    tam = (max(1, round(recorte.width * escala)), max(1, round(recorte.height * escala)))
    recorte = recorte.resize(tam, Image.LANCZOS)
    mascara = mascara.resize(tam, Image.LANCZOS)
    if escala > 1.3:  # fotos pequeñas: recuperar algo de nitidez tras ampliar
        recorte = recorte.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))

    lienzo = Image.new("RGB", (LADO, LADO), FONDO)
    x = (LADO - tam[0]) // 2
    y = (LADO - tam[1]) // 2

    # Sombra de contacto: una elipse difuminada bajo la base del producto.
    sombra = Image.new("L", (LADO, LADO), 0)
    d = ImageDraw.Draw(sombra)
    ancho = tam[0] * 0.86
    alto = max(14, tam[1] * 0.045)
    base = y + tam[1]
    d.ellipse((LADO / 2 - ancho / 2, base - alto / 2, LADO / 2 + ancho / 2, base + alto / 2), fill=70)
    sombra = sombra.filter(ImageFilter.GaussianBlur(alto * 0.8))
    lienzo.paste((60, 40, 70), (0, 0), sombra)

    lienzo.paste(recorte, (x, y), mascara)
    return lienzo


def comparativa(pares: list[tuple[Image.Image, Image.Image, str]], destino: Path) -> None:
    celda, pie = 300, 34
    filas = len(pares)
    hoja = Image.new("RGB", (celda * 2 + 30, filas * (celda + pie) + 50), (238, 234, 242))
    d = ImageDraw.Draw(hoja)
    try:
        fuente = ImageFont.truetype("DejaVuSans.ttf", 15)
        titulo = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except OSError:
        fuente = titulo = ImageFont.load_default()
    d.text((10, 14), "Antes", font=titulo, fill=(40, 20, 50))
    d.text((celda + 20, 14), "Después", font=titulo, fill=(40, 20, 50))
    for i, (antes, despues, nombre) in enumerate(pares):
        y = 50 + i * (celda + pie)
        for j, img in enumerate((antes, despues)):
            # El «antes» se muestra como lo enseña hoy el listado de Odoo: recorte cuadrado «cover».
            if j == 0:
                lado = min(img.size)
                img = img.crop(((img.width - lado) // 2, (img.height - lado) // 2,
                                (img.width + lado) // 2, (img.height + lado) // 2))
            img = img.resize((celda, celda), Image.LANCZOS)
            hoja.paste(img, (10 + j * (celda + 10), y))
        d.text((10, y + celda + 6), nombre[:70], font=fuente, fill=(60, 50, 70))
    hoja.save(destino, quality=85)


def main() -> int:
    salida = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "imagenes"
    (salida / "originales").mkdir(parents=True, exist_ok=True)
    (salida / "mejoradas").mkdir(parents=True, exist_ok=True)
    pares = []
    lista = productos()
    if not lista:
        print("No se encontraron productos en la tienda.", file=sys.stderr)
        return 1
    for pid, slug, nombre in lista:
        datos = descargar(f"{BASE}/web/image/product.template/{pid}/image_1920")
        original = Image.open(io.BytesIO(datos))
        ext = (original.format or "webp").lower()
        (salida / "originales" / f"{slug}.{ext}").write_bytes(datos)
        nueva = encuadrar(datos)
        nueva.save(salida / "mejoradas" / f"{slug}.jpg", quality=90, optimize=True, progressive=True)
        antes, _ = a_rgb(original)
        pares.append((antes, nueva, nombre))
        print(f"{pid:>4}  {original.size[0]}x{original.size[1]} -> {LADO}x{LADO}  {nombre}")
    comparativa(pares, salida / "comparativa.jpg")
    print(f"\n{len(pares)} imágenes en {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
