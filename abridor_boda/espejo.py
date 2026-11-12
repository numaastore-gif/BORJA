"""Espejo de regalo de boda, compañero del abridor: el mismo disco de Ø 75 × 10
mm con la misma cara del dibujo de los novios, «Marta y Borja» y «12/12/26»
(incrustados a ras, en otro color), y en la otra cara, en lugar del abridor,
el hueco para un cristal espejo de 50 × 50 × 1 mm.

  hueco    50,4 × 50,4 mm (0,2 mm de holgura por lado) y 1,1 mm de hondo: el
           espejo queda a ras con una capa fina de pegamento o cinta de doble
           cara. Esquinas con radio de 0,5 mm, que con esa holgura no tocan
           las esquinas vivas del cristal.
  sin imanes: con el espejo en la cara de atrás, no va a la nevera.

    python espejo.py
"""
import pathlib

import numpy as np
from manifold3d import Manifold

import abridor as A

AQUI = pathlib.Path(__file__).parent
ESPEJO = dict(lado=50.0, grosor=1.0, holgura=0.2, pegamento=0.1, radio=0.5)


def construir():
    d = A.DISCO
    g, r, c = d["grosor"], d["diametro"] / 2, d["chaflan"]
    disco = Manifold.batch_hull([Manifold.cylinder(g - 2 * c, r, r, 256).translate((0, 0, c)),
                                 Manifold.cylinder(g, r - c, r - c, 256)])
    e = ESPEJO
    lado = e["lado"] + 2 * e["holgura"]
    hondo = e["grosor"] + e["pegamento"]
    hueco = A.rect_redondeado(lado, lado, e["radio"]).extrude(hondo + 1).translate((0, 0, g - hondo))
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
    esquina = np.hypot(*(np.array([ESPEJO["lado"]] * 2) / 2 + ESPEJO["holgura"]))
    print("disco:", tc.is_watertight, np.round(tc.extents, 1), "| dibujo:", td.is_watertight,
          f"| pared en las esquinas del hueco: {A.DISCO['diametro'] / 2 - A.DISCO['chaflan'] - esquina:.1f} mm")
