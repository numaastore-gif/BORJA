"""Espejo de regalo de boda, compañero del abridor: el mismo disco de Ø 75 × 10
mm con la misma cara del dibujo de los novios, «Marta y Borja» y «12/12/2026»
(incrustados a ras, en otro color), y en la otra cara, en lugar del abridor,
el hueco para un cristal espejo redondo de Ø 50 × 1 mm.

  hueco    Ø 49,9 mm (ajustado a los espejos recibidos: con Ø 50,4 sobraba
           holgura por los lados) y 1,5 mm de hondo: el espejo de 1 mm queda
           0,5 mm hundido, con sitio para el pegamento o la cinta de doble cara.
  tapa     giratoria, como los espejos de bolsillo: un disco de Ø 75 × 3 mm
           sobre la cara del espejo que gira sobre un eje cerca del borde
           (a la derecha) y se aparta hacia un lado para descubrir el espejo.
           Mismo chaflán que el disco: cerrada, la junta es una línea fina.
  eje      pasador impreso (cabeza de Ø 6 a ras de la tapa, en un avellanado,
           y vástago de Ø 3): la tapa gira libre (agujero de Ø 3,4) y el
           pasador queda fijo en el disco (agujero de Ø 3,0, con una gota de
           pegamento). Sirve también un remache o un tornillo de M3.
  cierre   un par de imanes de Ø 8 × 2 mm al otro lado (izquierda), uno en el
           disco y otro escondido en la tapa: la mantienen cerrada.
  Tapa y pasador se imprimen con la cabeza / la cara de arriba sobre la cama.

    python espejo.py
"""
import pathlib

import numpy as np
from manifold3d import Manifold

import abridor as A

AQUI = pathlib.Path(__file__).parent
ESPEJO = dict(diametro=50.0, grosor=1.0, hueco=49.9, hondo=1.5)
IMANES_X = 30.8              # entre el hueco del espejo (r 24,95) y el borde
TAPA = dict(grosor=3.0)
EJE = dict(x=30.8, vastago=3.0, holgura=0.2, cabeza=6.0, alto_cabeza=1.2, en_disco=5.0)  # eje a la derecha


def construir():
    d = A.DISCO
    g, r, c = d["grosor"], d["diametro"] / 2, d["chaflan"]
    disco = Manifold.batch_hull([Manifold.cylinder(g - 2 * c, r, r, 256).translate((0, 0, c)),
                                 Manifold.cylinder(g, r - c, r - c, 256)])
    e = ESPEJO
    rh = e["hueco"] / 2
    hondo = e["hondo"]
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
    e = EJE
    eje = Manifold.cylinder(e["en_disco"] + 1, e["vastago"] / 2, e["vastago"] / 2, 48).translate((e["x"], 0, g - e["en_disco"]))
    disco = disco - hueco - iman(g) - eje
    return disco - dib, dib


def iman(z):
    """Alojamiento del imán de cierre (a la izquierda), abierto hacia arriba en la cara z."""
    im = A.IMAN
    r = (im["diametro"] + 2 * im["holgura"]) / 2
    h = im["alto"] + im["holgura"]
    return Manifold.cylinder(h + 1, r, r, 64).translate((-IMANES_X, 0, z - h))


def tapa():
    """Tapa en la posición de impresión: cara de arriba sobre la cama (z = 0) y
    la cara que toca el espejo arriba (z = grosor). El disco de la tapa es el
    reflejo del de abajo, así que el imán y el eje quedan en espejo (x → -x)."""
    d, t, e = A.DISCO, TAPA, EJE
    g, r, c = t["grosor"], d["diametro"] / 2, d["chaflan"]
    cuerpo = Manifold.batch_hull([Manifold.cylinder(g - c, r, r, 256).translate((0, 0, c)),
                                  Manifold.cylinder(g, r - c, r - c, 256)])
    # al darle la vuelta para imprimirla, la izquierda pasa a la derecha
    agujero = Manifold.cylinder(g + 2, e["vastago"] / 2 + e["holgura"], e["vastago"] / 2 + e["holgura"], 48) \
        .translate((-e["x"], 0, -1))
    avellanado = Manifold.cylinder(e["alto_cabeza"] + 1, e["cabeza"] / 2 + e["holgura"], e["cabeza"] / 2 + e["holgura"], 64) \
        .translate((-e["x"], 0, -1))
    return cuerpo - agujero - avellanado - iman(g).mirror((1, 0, 0))


def pasador():
    """Pasador del eje, con la cabeza sobre la cama."""
    e, t = EJE, TAPA
    largo = t["grosor"] - e["alto_cabeza"] + e["en_disco"] - 0.3
    cabeza = Manifold.cylinder(e["alto_cabeza"] - 0.1, e["cabeza"] / 2, e["cabeza"] / 2, 64)
    vastago = Manifold.cylinder(largo + 0.1, e["vastago"] / 2, e["vastago"] / 2, 48).translate((0, 0, e["alto_cabeza"] - 0.2))
    punta = Manifold.cylinder(0.4, e["vastago"] / 2, e["vastago"] / 2 - 0.4, 48).translate((0, 0, e["alto_cabeza"] - 0.1 + largo))
    return cabeza + vastago + punta


if __name__ == "__main__":
    cuerpo, dib = construir()
    tc, td = A.a_trimesh(cuerpo), A.a_trimesh(dib)
    tc.export(AQUI / "espejo_disco.stl")
    td.export(AQUI / "espejo_dibujo.stl")
    tc.export(AQUI / "espejo_boda.stl")   # una pieza: el dibujo grabado
    tt = A.a_trimesh(tapa())
    tt.export(AQUI / "espejo_tapa.stl")
    tp = A.a_trimesh(pasador())
    tp.export(AQUI / "espejo_pasador.stl")
    print("tapa:", tt.is_watertight, np.round(tt.extents, 1), "| pasador:", tp.is_watertight, np.round(tp.extents, 1))
    borde = ESPEJO["hueco"] / 2
    print("disco:", tc.is_watertight, np.round(tc.extents, 1), "| dibujo:", td.is_watertight,
          f"| borde alrededor del espejo: {A.DISCO['diametro'] / 2 - borde:.1f} mm")
