"""Genera el STL de una cubitera para una botella de vino.

Silueta calcada de la foto de la cubitera transparente de referencia y
escalada a sus medidas (20 x 20,5 x 24 cm): se ensancha de forma continua
desde un fondo pequeño y redondeado hasta la boca, que está cortada en curva
(baja en un lado y alta en el del asa). El asa es una ranura triangular
redondeada y simétrica, debajo va el texto en relieve siguiendo la pared, y en el fondo
hay un tope para que la botella quede recostada contra la pared alta.
Todas las medidas en mm.

    pip install numpy trimesh manifold3d matplotlib
    python cubitera.py
"""
import pathlib

import numpy as np
import trimesh
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from manifold3d import CrossSection, FillRule, Manifold, Mesh

# --- Parámetros -------------------------------------------------------------
# Semieje largo exterior según la altura, calcado de la foto de perfil.
PERFIL = [(0.0, 42.0), (3.0, 46.0), (6.0, 49.0), (9.9, 51.4), (12.4, 54.0),
          (17.4, 58.1), (22.4, 61.8), (27.3, 64.7), (37.3, 69.8), (47.2, 73.6),
          (57.1, 77.0), (67.1, 79.7), (77.0, 82.1), (87.0, 84.0), (96.9, 85.6),
          (106.8, 87.5), (116.8, 89.1), (126.7, 90.4), (136.6, 91.8), (146.6, 93.4),
          (156.5, 94.4), (166.5, 95.8), (176.4, 96.8), (183.9, 97.6), (216.1, 99.8),
          (226.1, 101.9), (236.0, 103.0), (240.0, 104.1), (260.0, 105.5)]
# Borde de la boca (x, z), también calcado: sube en curva hacia el asa.
BOCA = [(-98.2, 187.8), (-82.7, 191.8), (-66.6, 194.8), (-50.6, 197.8),
        (-34.5, 201.2), (-18.5, 204.7), (-2.4, 208.2), (13.6, 212.7),
        (29.7, 217.6), (45.7, 222.1), (61.8, 227.1), (77.8, 233.0),
        (93.9, 238.5), (103.0, 240.0)]
ANCHO_RELATIVO = 20.5 / 20.0  # semieje transversal / semieje largo
PARED = 3.0
FONDO = 4.0
# Asa: ranura triangular redondeada y simétrica (base abajo, vértice arriba).
# (u, v, radio) de los círculos que la envuelven; u a lo largo de la pared
# (0 = punta del lado alto), v hacia arriba.
ASA = [(-44.0, 6.0, 6.0), (44.0, 6.0, 6.0), (0.0, 15.0, 13.0)]
ASA_Z = 188.0          # altura del borde inferior de la ranura
TEXTO = "Jose y Valle"
FUENTE = pathlib.Path(__file__).with_name("Cinzel-Bold.ttf")  # OFL
LETRA = 12.0           # altura de las mayúsculas
RELIEVE = 0.8          # lo que sobresale el texto de la pared
TEXTO_Z = 170.0        # altura de la línea base del texto
TOPE = dict(x=-34.0, largo=16.0, ancho=30.0, alto=16.0)  # suplemento del fondo
BOTELLA_D = 82.0       # diámetro de la botella que abraza el tope
SEGMENTOS = 200


def semieje(z, offset=0.0):
    a = np.interp(z, *zip(*PERFIL))
    return a - offset, a * ANCHO_RELATIVO - offset


def solevado(pts, n_anillos):
    """Malla cerrada que une anillos de SEGMENTOS puntos, con tapa abajo y arriba."""
    n = SEGMENTOS
    caras = []
    for r in range(n_anillos - 1):
        for i in range(n):
            a, b = r * n + i, r * n + (i + 1) % n
            caras += [(a, b, b + n), (a, b + n, a + n)]
    abajo, arriba = len(pts), len(pts) + 1
    tapas = np.array([pts[:n].mean(0), pts[-n:].mean(0)])
    top = (n_anillos - 1) * n
    for i in range(n):
        caras.append((abajo, (i + 1) % n, i))
        caras.append((arriba, top + i, top + (i + 1) % n))
    verts = np.vstack([pts, tapas]).astype(np.float32)
    return Manifold(Mesh(vert_properties=verts, tri_verts=np.array(caras, dtype=np.uint32)))


def cuerpo(interior=False):
    """Sólido exterior, o el hueco interior (pared de grosor constante)."""
    z0 = FONDO if interior else 0.0
    zs = np.unique(np.concatenate([[z0], [z for z, _ in PERFIL if z > z0],
                                   np.arange(z0, PERFIL[-1][0], 4.0)]))
    t = np.linspace(0, 2 * np.pi, SEGMENTOS, endpoint=False)
    pts = []
    for z in zs:
        off = 0.0
        if interior:  # desplazamiento horizontal que da PARED medida en normal
            pend = (semieje(z + 1)[0] - semieje(z - 1)[0]) / 2
            off = PARED * np.hypot(1, pend)
        a, b = semieje(z, off)
        pts += [(a * np.cos(k), b * np.sin(k), z) for k in t]
    return solevado(np.array(pts), len(zs))


def bajo_la_boca():
    """Todo lo que queda por debajo del borde curvo de la boca."""
    zs = [z for _, z in BOCA]
    perfil = [(-300.0, -50.0), (300.0, -50.0), (300.0, zs[-1]), *BOCA[::-1], (-300.0, zs[0])]
    return (CrossSection([np.array(perfil)]).extrude(600)
            .rotate((90, 0, 0)).translate((0, 300, 0)))


def envolver(solido, z_base):
    """Enrolla un sólido plano (u, v, w) sobre la pared exterior: u recorre la
    pared desde la punta del lado alto hacia +y, v sube y w sale hacia fuera."""
    t = np.linspace(-np.pi / 2, np.pi / 2, 2001)

    def f(p):
        u, v, w = p
        z = z_base + v
        a, b = semieje(z)
        s = np.concatenate([[0], np.cumsum(np.hypot(-a * np.sin(t), b * np.cos(t))[1:] * np.diff(t))])
        s -= np.interp(0.0, t, s)
        k = np.interp(u, s, t)
        nx, ny = b * np.cos(k), a * np.sin(k)
        n = np.hypot(nx, ny)
        return (a * np.cos(k) + w * nx / n, b * np.sin(k) + w * ny / n, z)

    return solido.refine_to_length(1.0).warp(f)


def asa():
    """Ranura triangular redondeada que atraviesa la pared alta."""
    forma = CrossSection.batch_hull([CrossSection.circle(r, 64).translate((u, v))
                                     for u, v, r in ASA])
    return envolver(forma.extrude(16).translate((0, 0, -10)), ASA_Z)


def texto():
    """Letras en relieve bajo el asa."""
    fuente = FontProperties(fname=str(FUENTE))
    ruta = TextPath((0, 0), TEXTO, size=1.0, prop=fuente)
    escala = LETRA / TextPath((0, 0), "J", size=1.0, prop=fuente).get_extents().height
    ext = ruta.get_extents()
    polis = [p * escala for p in ruta.to_polygons() if len(p) > 2]
    letras = CrossSection(polis, FillRule.EvenOdd).translate(
        (-(ext.x0 + ext.width / 2) * escala, 0))
    return envolver(letras.extrude(RELIEVE + 2.0).translate((0, 0, -2.0)), TEXTO_Z)


def tope():
    """Calzo redondeado en el fondo; su cara hacia el lado alto es cóncava
    para que el culo de la botella encaje y la botella quede recostada."""
    x0, l, w, h = TOPE["x"], TOPE["largo"], TOPE["ancho"], TOPE["alto"]
    r = 4.0
    esferas = [Manifold.sphere(r, 32).translate((x0 + dx, dy, FONDO - r))
               for dx in (-l / 2 + r, l / 2 - r) for dy in (-w / 2 + r, w / 2 - r)]
    esferas += [Manifold.sphere(r, 32).translate((x0 - l / 4, dy, FONDO + h - r))
                for dy in (-w / 2 + 2 * r, w / 2 - 2 * r)]
    botella = Manifold.cylinder(200, BOTELLA_D / 2, BOTELLA_D / 2, 128) \
        .translate((x0 + l / 2 - 4 + BOTELLA_D / 2, 0, FONDO + 1.5))
    return Manifold.batch_hull(esferas) - botella


def construir():
    exterior = cuerpo() ^ bajo_la_boca()
    hueco = cuerpo(interior=True)
    solido = exterior - hueco + (tope() ^ exterior) + (texto() - hueco)
    solido = solido - asa()
    m = solido.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)


if __name__ == "__main__":
    malla = construir()
    malla.export(pathlib.Path(__file__).with_name("cubitera.stl"))
    print("estanca:", malla.is_watertight, "| cuerpos:", malla.body_count,
          "| volumen cm3:", round(malla.volume / 1000, 1))
    print("tamaño mm:", np.round(malla.extents, 1))
