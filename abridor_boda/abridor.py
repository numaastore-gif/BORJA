"""Abridor de regalo de boda: disco de Ø 75 mm, como los abridores imán
personalizados. En una cara, la que se pega a la nevera, el abridor redondo de
acero comprado encastrado y dos imanes de 8 × 2 mm a sus lados; en la otra,
la que queda a la vista, el dibujo de los novios en línea continua.

  disco    Ø 75 × 10 mm
  abridor  cara de los imanes: asiento redondo del grosor del abridor (queda a ras), hueco
           detrás de su boca para el borde de la chapa y agujeros guía para
           sus dos tornillos
  dibujo   cara a la vista, arriba: la línea del dibujo (dibujo_novios.png) vectorizada (su
           esqueleto con trazo uniforme) e incrustada a ras en la cara de
           atrás, en espejo para que se lea al darle la vuelta. En el 3MF es
           una pieza aparte de otro color; se imprime sobre la cama, así que
           queda plana y a ras
  textos   debajo del dibujo, «Marta y Borja» y «12/12/2026» en Great Vibes
           (caligráfica de boda, OFL), incrustados igual que el dibujo
  imanes   en la cara del abridor, a izquierda y derecha: Ø 8 × 2 mm con
           0,1 mm de holgura

MEDIDAS DEL ABRIDOR: son una estimación sacada de las fotos (proporción con
el disco de 75 mm); con el
abridor en la mano se ajustan en ABRIDOR y se vuelve a generar.
Medidas en mm.

    python abridor.py
"""
import pathlib

import cv2
import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, JoinType, Manifold, OpType
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from skimage.morphology import skeletonize

AQUI = pathlib.Path(__file__).parent

# --- Disco y dibujo ----------------------------------------------------------------------
DISCO = dict(diametro=75.0, grosor=10.0, chaflan=0.8)
ALTO_DIBUJO = 44.0           # dibujo arriba
CENTRO_DIBUJO = 10.0         # altura del centro del dibujo en la cara
# Nombres y fecha debajo del dibujo, en Great Vibes (caligráfica, OFL)
FUENTE = AQUI / "GreatVibes-Regular.ttf"
TEXTOS = [dict(texto="Marta y Borja", alto=8.0, y=-19.0), dict(texto="12/12/2026", alto=5.2, y=-28.5)]
ENGROSAR = 0.15              # se engordan los trazos finos de la caligrafía para que se impriman
TRAZO = 0.85                 # ancho real de la línea del dibujo: 2 líneas con boquilla de 0,4
HUECO_MIN = 0.25             # solo se cierran rendijas que el laminador no podría imprimir
INCRUSTE = 0.6               # hondo de la línea en la cara de atrás (3 capas)
BOTONES = [(50, 378, 26), (582, 378, 26)]  # flechas de la captura que se borran (x, y, radio en píxeles)

# --- Abridor comprado (estimación: COMPRUEBA CON EL ABRIDOR EN LA MANO) ---------------------
ABRIDOR = dict(diametro=50.0, grosor=2.5, boca=(25.0, 16.0), radio_boca=3.0, tornillos=18.5)
HOLGURA = 0.3                # en el diámetro del asiento
HUECO_CHAPA = 5.0            # hondo del hueco detrás de la boca del abridor (deja 1,5 mm de fondo)
GUIA_TORNILLO = dict(diametro=2.0, hondo=5.0)

# --- Imanes -----------------------------------------------------------------------------
IMAN = dict(diametro=8.0, alto=2.0, holgura=0.1, separacion=31.0)  # desde el centro del disco


def rect_redondeado(ancho, alto, radio):
    return CrossSection.square((ancho - 2 * radio, alto - 2 * radio), center=True).offset(radio, circular_segments=64)


def dibujo(ancho_mm):
    """Línea del dibujo en mm, centrada, con trazo uniforme TRAZO."""
    img = cv2.imread(str(AQUI / "dibujo_novios.png"), cv2.IMREAD_GRAYSCALE)
    for x, y, r in BOTONES:
        cv2.circle(img, (x, y), r, 255, -1)
    k = 4  # se trabaja a 4 veces la resolución para un trazo suave
    grande = cv2.resize(img, None, fx=k, fy=k, interpolation=cv2.INTER_CUBIC)
    linea = grande < 140
    linea = cv2.morphologyEx(linea.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)).astype(bool)
    esqueleto = skeletonize(linea)
    mm_px = ancho_mm / img.shape[1] / k
    r = max(int(round(TRAZO / 2 / mm_px)), 1)
    trazo = cv2.dilate(esqueleto.astype(np.uint8) * 255, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    # los huecos entre líneas más estrechos que una línea de boquilla (0,45 mm)
    # no se imprimirían limpios: se cierran
    h = max(int(round(HUECO_MIN / mm_px)), 1) | 1
    trazo = cv2.morphologyEx(trazo, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (h, h)))
    contornos, _ = cv2.findContours(trazo, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    polis = [c[:, 0, :].astype(float) * (mm_px, -mm_px) for c in contornos if len(c) >= 3]
    c = CrossSection(polis, FillRule.EvenOdd).simplify(0.02)
    x0, y0, x1, y1 = c.bounds()
    return c.translate((-(x0 + x1) / 2, -(y0 + y1) / 2))


def dibujo_a_tamano(alto):
    """El dibujo con ALTO de alto y el trazo TRAZO ya a ese tamaño (el trazo se
    aplica después de escalar, no antes, para que mida lo que dice TRAZO)."""
    x0, y0, x1, y1 = dibujo(100.0).bounds()
    return dibujo(100.0 * alto / (y1 - y0))


def texto(cadena, alto):
    """Texto caligráfico con su caja centrada en x y en y = 0; «alto» es la
    altura total de la línea (de lo más bajo a lo más alto)."""
    prop = FontProperties(fname=str(FUENTE))
    ruta = TextPath((0, 0), cadena, size=1.0, prop=prop)
    c = CrossSection([p for p in ruta.to_polygons() if len(p) > 2], FillRule.EvenOdd)
    x0, y0, x1, y1 = c.bounds()
    c = c.translate((-(x0 + x1) / 2, -(y0 + y1) / 2)).scale((alto / (y1 - y0), alto / (y1 - y0)))
    return c.offset(ENGROSAR, JoinType.Round)


def construir():
    d = DISCO
    g, r, c = d["grosor"], d["diametro"] / 2, d["chaflan"]
    # disco con los dos cantos achaflanados
    disco = Manifold.batch_hull([Manifold.cylinder(g - 2 * c, r, r, 256).translate((0, 0, c)),
                                 Manifold.cylinder(g, r - c, r - c, 256)])
    # abridor delante (arriba, z = g)
    a = ABRIDOR
    asiento = Manifold.cylinder(a["grosor"] + 1, (a["diametro"] + HOLGURA) / 2, (a["diametro"] + HOLGURA) / 2, 180) \
        .translate((0, 0, g - a["grosor"]))
    bw, bh = a["boca"]
    chapa = rect_redondeado(bw + 2, bh + 4, a["radio_boca"] + 1).extrude(HUECO_CHAPA + 1) \
        .translate((0, 0, g - a["grosor"] - HUECO_CHAPA))
    guias = [Manifold.cylinder(GUIA_TORNILLO["hondo"] + 1, GUIA_TORNILLO["diametro"] / 2, GUIA_TORNILLO["diametro"] / 2, 32)
             .translate((0, s * a["tornillos"], g - a["grosor"] - GUIA_TORNILLO["hondo"])) for s in (-1, 1)]
    # imanes en la cara del abridor (z = g), a izquierda y derecha
    im = IMAN
    r_im = (im["diametro"] + 2 * im["holgura"]) / 2
    imanes = [Manifold.cylinder(im["alto"] + im["holgura"] + 1, r_im, r_im, 64)
              .translate((s * im["separacion"], 0, g - im["alto"] - im["holgura"])) for s in (-1, 1)]
    # dibujo y textos en la cara a la vista (z = 0), en espejo (se mira desde
    # ese lado), incrustados a ras
    lineas = dibujo_a_tamano(ALTO_DIBUJO).translate((0, CENTRO_DIBUJO))
    for t in TEXTOS:
        lineas = lineas + texto(t["texto"], t["alto"]).translate((0, t["y"]))
    lineas = lineas.mirror((1, 0))
    dib = lineas.extrude(INCRUSTE + 1).translate((0, 0, -1)) ^ disco
    disco = disco - asiento - chapa - Manifold.batch_boolean(guias + imanes, OpType.Add)
    cuerpo = disco - dib          # con el hueco del dibujo (3MF de dos colores)
    return cuerpo, dib, disco     # disco: una pieza, de un color (sin el dibujo)


def a_trimesh(m):
    s = m.to_mesh()
    return trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)


if __name__ == "__main__":
    cuerpo, dib, entero = construir()
    tp, tr = a_trimesh(cuerpo), a_trimesh(dib)
    tp.export(AQUI / "abridor_placa.stl")
    tr.export(AQUI / "abridor_dibujo.stl")
    # una pieza: el dibujo grabado en la cara de atrás
    a_trimesh(cuerpo).export(AQUI / "abridor_boda.stl")
    print("placa:", tp.is_watertight, np.round(tp.extents, 1), "| dibujo:", tr.is_watertight, np.round(tr.extents, 1),
          "cuerpos", tr.body_count)
