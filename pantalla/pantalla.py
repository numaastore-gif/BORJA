"""Pantalla colgante tipo campana orgánica para imprimir en modo jarrón con
piel difusa (estilo elden.designs), y anillo adaptador para portalámparas E27
con aro roscado.

  pantalla   sólido cerrado: Bambu Studio en modo jarrón imprime solo su
             pared exterior en espiral, sin fondo (0 capas inferiores) y con
             la boca del cuello abierta. Falda casi vertical abajo, cuerpo a
             40°, hombro que se redondea hasta un cuello recto. La planta se
             ondula en lóbulos suaves que crecen hacia el borde y giran al
             subir. Ninguna parte pasa de VOLADIZO_MAX de inclinación.
  anillo     se mete por dentro de la pantalla y sube por el cuello: arriba
             queda una tapa con el agujero del E27 (el aro del portalámparas
             aprieta por encima) y abajo un cono a 45° que se encaja en el
             hombro y sostiene el peso de la pantalla. Impresión normal, con la
             tapa sobre la cama y sin soportes.

Medidas en mm.

    python pantalla.py            # pantalla_jarron.stl y anillo_e27.stl, para imprimir
    python pantalla.py --vista    # vista_*.stl, ligeras y montadas, para el visor
"""
import pathlib
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, Mesh, triangulate

AQUI = pathlib.Path(__file__).parent

# --- Pantalla ---------------------------------------------------------------------------
R_BORDE = 136.0        # radio medio del borde de abajo (Ø ~272, con lóbulos ~290)
R_CUELLO = 31.0        # cuello: Ø 62 por fuera
ALTO_CUELLO = 12.0
ANGULOS = [(0.0, 6.0), (0.35, 30.0), (0.93, 44.0), (1.0, 0.0)]  # (fracción del cuerpo, grados desde la vertical): convexa hasta el cuello
LOBULOS = [(3, 0.065, 0.3, 0.9), (5, 0.02, 2.1, -0.6)]  # (número, amplitud en el borde, fase, giro total)
VOLADIZO_MAX = 45.0
VISTA = "--vista" in sys.argv   # versión ligera para el visor, montada
PUNTOS = 240 if VISTA else 720
PASO_Z = 2.0 if VISTA else 0.5

# --- Modo jarrón ------------------------------------------------------------------------
PARED = 0.6            # ancho de línea de la pared en modo jarrón (boquilla 0,4)
PIEL = 0.3             # grosor de la piel difusa

# --- Anillo E27 -------------------------------------------------------------------------
AGUJERO_E27 = 40.5     # rosca exterior del portalámparas: Ø 40 mm
TAPA = 3.0
PARED_ANILLO = 3.0
HOLGURA = 0.3
CONO = 7.0              # el cono del anillo se ensancha 7 mm a 45°


def suave(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def angulo(t):
    """Inclinación de la pared (grados desde la vertical) en la fracción t del cuerpo."""
    for (t0, a0), (t1, a1) in zip(ANGULOS, ANGULOS[1:]):
        if t <= t1:
            return a0 + (a1 - a0) * suave((t - t0) / (t1 - t0))
    return ANGULOS[-1][1]


def perfil():
    """Radio medio r(z) del cuerpo, desde el borde (z = 0) hasta el cuello."""
    ts = np.linspace(0, 1, 2001)
    pend = np.tan(np.radians([angulo(t) for t in ts]))
    # alto del cuerpo para que el radio baje exactamente de R_BORDE a R_CUELLO
    alto = (R_BORDE - R_CUELLO) / np.trapezoid(pend, ts)
    r = R_BORDE - np.concatenate([[0], np.cumsum((pend[1:] + pend[:-1]) / 2 * np.diff(ts))]) * alto
    return ts * alto, r, alto


Z_CUERPO, R_CUERPO, ALTO_CUERPO = perfil()
ALTO = ALTO_CUERPO + ALTO_CUELLO


def anillo_planta(z):
    """Contorno en planta a la altura z (PUNTOS puntos, antihorario)."""
    th = np.linspace(0, 2 * np.pi, PUNTOS, endpoint=False)
    if z >= ALTO_CUERPO:
        r = np.full_like(th, R_CUELLO)
    else:
        t = z / ALTO_CUERPO
        r0 = np.interp(z, Z_CUERPO, R_CUERPO)
        f = np.zeros_like(th)
        for n, a, fase, giro in LOBULOS:
            f += a * (1 - suave(t / 0.85)) * np.cos(n * th + fase + giro * t)
        r = r0 * (1 + f)
    return np.c_[r * np.cos(th), r * np.sin(th)]


def pantalla():
    zs = np.unique(np.r_[np.arange(0, ALTO, PASO_Z), ALTO])
    anillos = [anillo_planta(z) for z in zs]
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
    return m, zs, anillos


def voladizo_max(zs, anillos):
    """Mayor inclinación de la pared (grados desde la vertical) en todo el contorno."""
    peor = 0.0
    for z0, z1, a0, a1 in zip(zs, zs[1:], anillos, anillos[1:]):
        d = np.linalg.norm(a1, axis=1) - np.linalg.norm(a0, axis=1)
        peor = max(peor, np.degrees(np.arctan(np.abs(d).max() / (z1 - z0))))
    return peor


def anillo_e27():
    """Adaptador, en la posición de montaje (tapa arriba, a ras de la boca del
    cuello). El cono de abajo apoya en la pared de la pantalla justo donde su
    radio interior iguala al del cono, así el anillo queda a la altura justa."""
    r_tubo = R_CUELLO - PARED - PIEL - HOLGURA          # lo más estrecho por dentro del cuello
    r_cono = r_tubo + CONO
    # altura donde la pantalla, por dentro, mide r_cono
    r_dentro = R_CUERPO - PARED - PIEL
    z_apoyo = np.interp(r_cono, r_dentro[::-1], Z_CUERPO[::-1])
    z0 = z_apoyo + CONO                                 # arranque del tubo
    tubo = Manifold.cylinder(ALTO - z0, r_tubo, r_tubo, 180).translate((0, 0, z0))
    cono = Manifold.cylinder(CONO, r_cono, r_tubo, 180).translate((0, 0, z_apoyo))
    hueco = Manifold.cylinder(ALTO, r_tubo - PARED_ANILLO, r_tubo - PARED_ANILLO, 180).translate((0, 0, z_apoyo - 1))
    hueco = hueco ^ Manifold.cube((200, 200, ALTO - TAPA - z_apoyo + 1)).translate((-100, -100, z_apoyo - 1))
    e27 = Manifold.cylinder(TAPA + 2, AGUJERO_E27 / 2, AGUJERO_E27 / 2, 180).translate((0, 0, ALTO - TAPA - 1))
    return tubo + cono - hueco - e27, r_tubo, z_apoyo


def a_trimesh(m):
    s = m.to_mesh()
    return trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)


if __name__ == "__main__":
    if VISTA:  # pantalla y anillo en su sitio, para el visor
        p, _, _ = pantalla()
        a, _, _ = anillo_e27()
        a_trimesh(p).export(AQUI / "vista_pantalla.stl")
        a_trimesh(a).export(AQUI / "vista_anillo.stl")
        sys.exit()
    p, zs, anillos = pantalla()
    tp = a_trimesh(p)
    tp.export(AQUI / "pantalla_jarron.stl")
    print(f"pantalla: estanca={tp.is_watertight} tamaño={np.round(tp.extents, 1)} "
          f"voladizo máximo={voladizo_max(zs, anillos):.1f}° alto del cuerpo={ALTO_CUERPO:.1f}")
    a, r_tubo, z_apoyo = anillo_e27()
    ta = a_trimesh(a)
    # para imprimir: tapa sobre la cama
    ta.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    ta.apply_translation([0, 0, -ta.bounds[0][2]])
    ta.export(AQUI / "anillo_e27.stl")
    print(f"anillo: estanca={ta.is_watertight} tamaño={np.round(ta.extents, 1)} tubo Ø {2 * r_tubo:.1f} "
          f"(cuello por dentro Ø {2 * (R_CUELLO - PARED):.1f}, con piel Ø {2 * (R_CUELLO - PARED - PIEL):.1f}); "
          f"largo {ALTO - z_apoyo:.1f} mm, apoya {ALTO_CUERPO - z_apoyo:.1f} mm por debajo del cuello")
