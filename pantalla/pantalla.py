"""Pantalla colgante tipo campana, lisa, para imprimir del revés en modo jarrón
con piel difusa (estilo elden.designs), con el agujero del portalámparas E27.

Se imprime boca arriba: la parte de arriba de la pantalla (un disco plano)
va sobre la cama y la falda sube. En modo jarrón Bambu Studio hace primero
las capas inferiores macizas (el disco, con el agujero del E27, donde aprieta
el aro del portalámparas) y luego solo la pared exterior en espiral, abierta
por la boca. Perfil convexo: casi vertical en la falda y a 44° junto al disco,
así que en esta postura ninguna parte pasa de VOLADIZO_MAX. Sin lóbulos ni
cuello; la boca se ondula en ondas suaves que crecen hacia el borde.

    python pantalla.py            # pantalla_jarron.stl, para imprimir
    python pantalla.py --vista    # vista_pantalla.stl, ligera, para el visor
"""
import pathlib
import sys

import numpy as np
import trimesh
from manifold3d import Manifold, Mesh, triangulate

AQUI = pathlib.Path(__file__).parent
VISTA = "--vista" in sys.argv

R_BORDE = 140.0        # radio de la boca (Ø 280)
R_ARRIBA = 34.0        # disco plano de arriba (Ø 68): apoyo en la cama y del aro del E27
ANGULOS = [(0.0, 6.0), (0.35, 30.0), (1.0, 44.0)]  # (fracción desde la boca, grados desde la vertical)
VOLADIZO_MAX = 45.0
# Ondas en la boca: la planta se ondula en ONDAS.numero ondas suaves que nacen
# a media altura y crecen hasta la boca (amplitud radial en mm)
ONDAS = dict(numero=12, amplitud=9.0, desde=0.45)
AGUJERO_E27 = 40.5     # rosca exterior del portalámparas: Ø 40 mm
CAPA = 0.2
CAPAS_DISCO = 8        # capas inferiores del modo jarrón: disco de 1,6 mm
DISCO = CAPA * CAPAS_DISCO
PUNTOS = 240 if VISTA else 720
PASO_Z = 2.0 if VISTA else 0.5


def suave(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def angulo(t):
    for (t0, a0), (t1, a1) in zip(ANGULOS, ANGULOS[1:]):
        if t <= t1:
            return a0 + (a1 - a0) * suave((t - t0) / (t1 - t0))
    return ANGULOS[-1][1]


def perfil():
    """Radio r según la altura de impresión z (z = 0 el disco sobre la cama)."""
    ts = np.linspace(0, 1, 4001)                      # desde la boca hacia arriba
    pend = np.tan(np.radians([angulo(t) for t in ts]))
    alto = (R_BORDE - R_ARRIBA) / np.trapezoid(pend, ts)
    r = R_BORDE - np.concatenate([[0], np.cumsum((pend[1:] + pend[:-1]) / 2 * np.diff(ts))]) * alto
    z = alto - ts * alto                              # del revés: la boca arriba
    return z[::-1], r[::-1], alto


Z, R, ALTO = perfil()


def pantalla():
    th = np.linspace(0, 2 * np.pi, PUNTOS, endpoint=False)
    zs = np.unique(np.r_[np.arange(0, ALTO, PASO_Z), ALTO])
    def radio(z):
        s = suave((z / ALTO - ONDAS["desde"]) / (1 - ONDAS["desde"]))   # 0 lejos de la boca, 1 en la boca
        return np.interp(z, Z, R) + ONDAS["amplitud"] * s * np.cos(ONDAS["numero"] * th)
    anillos = [radio(z)[:, None] * np.c_[np.cos(th), np.sin(th)] for z in zs]
    n = PUNTOS
    pts = np.vstack([np.c_[a, np.full(n, z)] for a, z in zip(anillos, zs)])
    caras = []
    for f in range(len(zs) - 1):
        i = f * n + np.arange(n)
        j = f * n + (np.arange(n) + 1) % n
        caras += [np.c_[i, j, j + n], np.c_[i, j + n, i + n]]
    caras.append(triangulate([anillos[0]])[:, ::-1])
    caras.append(triangulate([anillos[-1]]) + (len(zs) - 1) * n)
    m = Manifold(Mesh(vert_properties=pts.astype(np.float32), tri_verts=np.vstack(caras).astype(np.uint32)))
    # agujero del E27 solo en el disco (las capas inferiores); más arriba el
    # modo jarrón solo hace la pared exterior
    agujero = Manifold.cylinder(DISCO + 1, AGUJERO_E27 / 2, AGUJERO_E27 / 2, 180).translate((0, 0, -1))
    return m - agujero, zs, anillos


def voladizo_max(zs, anillos):
    peor = 0.0
    for z0, z1, a0, a1 in zip(zs, zs[1:], anillos, anillos[1:]):
        d = np.linalg.norm(a1, axis=1) - np.linalg.norm(a0, axis=1)
        peor = max(peor, np.degrees(np.arctan(np.abs(d).max() / (z1 - z0))))
    return peor


def a_trimesh(m):
    s = m.to_mesh()
    return trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)


if __name__ == "__main__":
    p, zs, anillos = pantalla()
    t = a_trimesh(p)
    if VISTA:  # en la postura de impresión, como se verá en Bambu Studio
        t.export(AQUI / "vista_pantalla.stl")
    else:
        t.export(AQUI / "pantalla_jarron.stl")
    print(f"pantalla: estanca={t.is_watertight} tamaño={np.round(t.extents, 1)} "
          f"voladizo máximo={voladizo_max(zs, anillos):.1f}° disco Ø {2 * R_ARRIBA:.0f} con agujero Ø {AGUJERO_E27}")
