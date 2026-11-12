"""Espejo de regalo de boda, compañero del abridor: el mismo disco de Ø 75 × 10
mm con la misma cara del dibujo de los novios, «Marta y Borja» y «12/12/2026»
(incrustados a ras, en otro color), y en la otra cara, en lugar del abridor,
el hueco para un cristal espejo redondo de Ø 50 × 1 mm.

  hueco    Ø 50,4 mm (0,2 mm de holgura por lado) y 1,1 mm de hondo: el espejo
           queda a ras con una capa fina de pegamento o cinta de doble cara.
  sin imanes: con el espejo en la cara de atrás, no va a la nevera.

    python espejo.py
"""
import pathlib

import numpy as np
from manifold3d import Manifold

import abridor as A

AQUI = pathlib.Path(__file__).parent
ESPEJO = dict(diametro=50.0, grosor=1.0, holgura=0.2, pegamento=0.1)


def construir():
    d = A.DISCO
    g, r, c = d["grosor"], d["diametro"] / 2, d["chaflan"]
    disco = Manifold.batch_hull([Manifold.cylinder(g - 2 * c, r, r, 256).translate((0, 0, c)),
                                 Manifold.cylinder(g, r - c, r - c, 256)])
    e = ESPEJO
    rh = e["diametro"] / 2 + e["holgura"]
    hondo = e["grosor"] + e["pegamento"]
    hueco = Manifold.cylinder(hondo + 1, rh, rh, 256).translate((0, 0, g - hondo))
    # la misma cara del dibujo que el abridor
    lineas = A.dibujo(100.0)
    x0, y0, x1, y1 = lineas.bounds()
    k = A.ALTO_DIBUJO / (y1 - y0)
    lineas = lineas.scale((k, k)).translate((0, A.CENTRO_DIBUJO))
    for t in A.TEXTOS:
        lineas = lineas + A.texto(t["texto"], t["alto"]).translate((0, t["y"]))
    lineas = lineas.mirror((1, 0))
    dib = lineas.extrude(A.INCRUSTE + 1).translate((0, 0, -1)) ^ disco
    disco = disco - hueco
    return disco - dib, dib


if __name__ == "__main__":
    cuerpo, dib = construir()
    tc, td = A.a_trimesh(cuerpo), A.a_trimesh(dib)
    tc.export(AQUI / "espejo_disco.stl")
    td.export(AQUI / "espejo_dibujo.stl")
    tc.export(AQUI / "espejo_boda.stl")   # una pieza: el dibujo grabado
    borde = ESPEJO["diametro"] / 2 + ESPEJO["holgura"]
    print("disco:", tc.is_watertight, np.round(tc.extents, 1), "| dibujo:", td.is_watertight,
          f"| borde alrededor del espejo: {A.DISCO['diametro'] / 2 - borde:.1f} mm")
