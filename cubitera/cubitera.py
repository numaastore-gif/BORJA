"""Genera el STL de una cubitera para una botella de vino.

Cuerpo ovalado que se abre hacia arriba, fondo redondeado, boca cortada en
diagonal y un agujero-asa en el lado alto. Todas las medidas en mm.

    pip install numpy trimesh manifold3d
    python cubitera.py
"""
import numpy as np
import trimesh
from manifold3d import Manifold, Mesh

# --- Parámetros -------------------------------------------------------------
ALTO_MAX = 240.0      # altura en el lado del asa
ALTO_MIN = 180.0      # altura en el lado bajo
BOCA = (170.0, 140.0)  # ejes exteriores del óvalo arriba (largo, ancho)
BASE = (125.0, 105.0)  # ejes exteriores del óvalo abajo
RADIO_FONDO = 25.0    # redondeo entre pared y fondo
PARED = 3.0           # grosor de la pared
FONDO = 4.0           # grosor del fondo
ASA = (55.0, 26.0)    # agujero del asa (ancho, alto)
ASA_BAJO_BORDE = 14.0  # distancia del borde al agujero
SEGMENTOS = 160


def cuerpo(offset=0.0, z0=0.0, altura=ALTO_MAX + 20):
    """Sólido convexo ovalado; offset>0 lo encoge (para el hueco interior)."""
    R = RADIO_FONDO - offset
    zs = list(z0 + R - R * np.cos(np.linspace(0, np.pi / 2, 24)))
    zs.append(altura)
    t = np.linspace(0, 2 * np.pi, SEGMENTOS, endpoint=False)
    pts = []
    for z in zs:
        f = min(z / ALTO_MAX, 1.3)  # conicidad lineal
        a = (BASE[0] + (BOCA[0] - BASE[0]) * f) / 2 - offset
        b = (BASE[1] + (BOCA[1] - BASE[1]) * f) / 2 - offset
        dz = z - z0
        if dz < R:  # redondeo del fondo
            encoge = R - np.sqrt(max(R * R - (R - dz) ** 2, 0.0))
            a, b = a - encoge, b - encoge
        a, b = max(a, 0.5), max(b, 0.5)
        pts += [(a * np.cos(k), b * np.sin(k), z) for k in t]
    return Manifold.hull_points(np.array(pts))


def corte_diagonal():
    """Semiespacio bajo el plano inclinado de la boca."""
    semi = BOCA[0] / 2
    pendiente = (ALTO_MAX - ALTO_MIN) / (2 * semi)
    medio = (ALTO_MAX + ALTO_MIN) / 2
    caja = Manifold.cube((1000, 1000, 1000), center=True).translate((0, 0, -500))
    ang = np.degrees(np.arctan(pendiente))
    return caja.rotate((0, -ang, 0)).translate((0, 0, medio)), pendiente, medio


def asa(pendiente, medio):
    x = BOCA[0] / 2 - 8
    z = medio + pendiente * x - ASA_BAJO_BORDE - ASA[1] / 2
    cil = Manifold.cylinder(80, 1.0, 1.0, 96, center=True)  # eje Z
    cil = cil.scale((ASA[1] / 2, ASA[0] / 2, 1)).rotate((0, 90, 0))
    return cil.translate((x, 0, z))


def construir():
    corte, pendiente, medio = corte_diagonal()
    exterior = cuerpo() ^ corte
    interior = cuerpo(offset=PARED, z0=FONDO)
    solido = exterior - interior - asa(pendiente, medio)
    m = solido.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts)


if __name__ == "__main__":
    malla = construir()
    malla.export("cubitera.stl")
    print("estanca:", malla.is_watertight, "| volumen cm3:", round(malla.volume / 1000, 1))
    print("tamaño mm:", np.round(malla.extents, 1))
