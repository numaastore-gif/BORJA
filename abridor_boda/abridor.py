"""Abridor de regalo de boda: placa con el dibujo de los novios en línea
continua en relieve, el asiento para el abridor redondo de acero comprado
(encastrado a ras, con su hueco detrás para la chapa) y dos imanes de 8 × 2 mm
por detrás, a los lados del abridor, como en la foto de referencia.

  placa    rectángulo redondeado; el dibujo arriba y el abridor abajo
  dibujo   la línea del dibujo (dibujo_novios.png) vectorizada: se saca su
           esqueleto y se le da un trazo uniforme, en relieve sobre la placa
           (pieza aparte en el 3MF, para imprimirla en otro color)
  abridor  asiento redondo del grosor del abridor, hueco detrás de su boca
           para que entre el borde de la chapa y dos agujeros guía para sus
           tornillos
  imanes   dos alojamientos de Ø 8 × 2 mm (con 0,1 mm de holgura) por detrás

MEDIDAS DEL ABRIDOR: son una estimación hecha a partir de la foto; con el
abridor en la mano se ajustan en ABRIDOR y se vuelve a generar.
Medidas en mm.

    python abridor.py
"""
import pathlib

import cv2
import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, Manifold, OpType
from skimage.morphology import skeletonize

AQUI = pathlib.Path(__file__).parent

# --- Placa y dibujo ---------------------------------------------------------------------
PLACA = dict(ancho=110.0, alto=170.0, grosor=9.0, radio=10.0)
MARGEN = 5.0                 # borde liso alrededor del dibujo
ZONA_DIBUJO = 120.0          # alto que ocupa el dibujo (arriba)
TRAZO = 1.1                  # ancho de la línea del dibujo
RELIEVE = 0.8                # cuánto sobresale la línea
BOTONES = [(50, 378, 26), (582, 378, 26)]  # flechas de la captura que se borran (x, y, radio en píxeles)

# --- Abridor comprado (estimación: COMPRUEBA CON EL ABRIDOR EN LA MANO) ---------------------
ABRIDOR = dict(diametro=41.0, grosor=2.5, boca=(24.0, 17.0), radio_boca=3.0, tornillos=15.5, centro_y=30.0)
HOLGURA = 0.3                # en el diámetro del asiento
HUECO_CHAPA = 5.0            # hondo del hueco detrás de la boca del abridor (deja 1,5 mm de fondo)
GUIA_TORNILLO = dict(diametro=2.0, hondo=5.0)

# --- Imanes -----------------------------------------------------------------------------
IMAN = dict(diametro=8.0, alto=2.0, holgura=0.1, separacion=31.0)  # separación desde el centro del abridor


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
    contornos, _ = cv2.findContours(trazo, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    polis = [c[:, 0, :].astype(float) * (mm_px, -mm_px) for c in contornos if len(c) >= 3]
    c = CrossSection(polis, FillRule.EvenOdd).simplify(0.02)
    x0, y0, x1, y1 = c.bounds()
    return c.translate((-(x0 + x1) / 2, -(y0 + y1) / 2))


def construir():
    p = PLACA
    g = p["grosor"]
    placa = rect_redondeado(p["ancho"], p["alto"], p["radio"]).extrude(g)
    # dibujo arriba, dentro del margen
    ancho_dib = p["ancho"] - 2 * MARGEN
    lineas = dibujo(ancho_dib)
    x0, y0, x1, y1 = lineas.bounds()
    escala = min(1.0, ZONA_DIBUJO / (y1 - y0))
    lineas = lineas.scale((escala, escala))
    y_dib = p["alto"] / 2 - MARGEN - ZONA_DIBUJO / 2
    lineas = lineas.translate((0, y_dib)) ^ rect_redondeado(p["ancho"] - 2 * MARGEN, p["alto"] - 2 * MARGEN, p["radio"] - MARGEN / 2)
    relieve = lineas.extrude(RELIEVE + 0.5).translate((0, 0, g - 0.5))
    # abridor
    a = ABRIDOR
    cy = -p["alto"] / 2 + a["centro_y"]
    asiento = Manifold.cylinder(a["grosor"] + 1, (a["diametro"] + HOLGURA) / 2, (a["diametro"] + HOLGURA) / 2, 180) \
        .translate((0, cy, g - a["grosor"]))
    bw, bh = a["boca"]
    chapa = rect_redondeado(bw + 2, bh + 4, a["radio_boca"] + 1).extrude(HUECO_CHAPA + 1) \
        .translate((0, cy, g - a["grosor"] - HUECO_CHAPA))
    guias = [Manifold.cylinder(GUIA_TORNILLO["hondo"] + 1, GUIA_TORNILLO["diametro"] / 2, GUIA_TORNILLO["diametro"] / 2, 32)
             .translate((0, cy + s * a["tornillos"], g - a["grosor"] - GUIA_TORNILLO["hondo"])) for s in (-1, 1)]
    # imanes por detrás, a los lados del abridor
    im = IMAN
    r_im = (im["diametro"] + 2 * im["holgura"]) / 2
    imanes = [Manifold.cylinder(im["alto"] + im["holgura"] + 1, r_im, r_im, 64).translate((s * im["separacion"], cy, -1))
              for s in (-1, 1)]
    placa = placa - asiento - chapa - Manifold.batch_boolean(guias + imanes, OpType.Add)
    # en una pieza: la línea entra 0,5 mm en la placa y se funde con ella
    junta = placa + (relieve - asiento)
    # para el 3MF de dos colores: la línea solo por encima de la placa
    relieve = relieve - placa - asiento
    return placa, relieve, junta


def a_trimesh(m):
    s = m.to_mesh()
    return trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)


if __name__ == "__main__":
    placa, relieve, junta = construir()
    tp, tr = a_trimesh(placa), a_trimesh(relieve)
    tp.export(AQUI / "abridor_placa.stl")
    tr.export(AQUI / "abridor_dibujo.stl")
    a_trimesh(junta).export(AQUI / "abridor_boda.stl")
    print("placa:", tp.is_watertight, np.round(tp.extents, 1), "| dibujo:", tr.is_watertight, np.round(tr.extents, 1),
          "cuerpos", tr.body_count)
