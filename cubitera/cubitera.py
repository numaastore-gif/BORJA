"""Genera el STL de una cubitera para una botella de vino.

Copia la silueta de la cubitera transparente de referencia: óvalo panzudo que
se ensancha hasta media altura y se cierra un poco en la boca, fondo plano con
esquinas muy redondeadas, boca cortada en diagonal, asa ranurada en el lado
alto y un tope en el fondo (lado bajo) donde apoya el culo de la botella para
que quede recostada contra la pared alta. Bajo el asa lleva el texto en
relieve siguiendo la curva de la pared. Todas las medidas en mm.

    pip install numpy trimesh manifold3d matplotlib
    python cubitera.py
"""
import numpy as np
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
import trimesh
from manifold3d import CrossSection, FillRule, Manifold, Mesh

# --- Parámetros -------------------------------------------------------------
# Medidas del producto: 20,5 x 20 x 24 cm (largo x ancho x alto).
ALTO_MAX = 240.0       # altura en el lado del asa
ALTO_MIN = 162.0       # altura en el lado bajo
# Semieje largo exterior de la pared (antes del redondeo del fondo) según la
# altura relativa, medido sobre la foto de referencia.
PERFIL = [(0.0, 90.2), (0.1, 94.3), (0.2, 97.9), (0.4, 102.0),
          (0.6, 102.5), (0.8, 99.4), (1.0, 95.3), (1.2, 90.2)]
ANCHO_RELATIVO = 200 / 205  # semieje corto / semieje largo
RADIO_FONDO = (30.0, 48.0)  # redondeo elíptico pared-fondo (horizontal, vertical)
PARED = 3.0
FONDO = 4.0
ASA = (72.0, 24.0)     # ranura del asa (ancho, alto)
ASA_BAJO_BORDE = 15.0  # distancia del borde al techo de la ranura
TEXTO = "Jose y Valle"
LETRA = 11.0           # altura de las mayúsculas
RELIEVE = 0.8          # lo que sobresale el texto de la pared
TEXTO_BAJO_ASA = 10.0  # hueco entre la ranura y lo alto de las letras
TOPE = dict(x=-40.0, largo=24.0, ancho=40.0, alto=20.0)  # suplemento del fondo
BOTELLA_D = 82.0       # diámetro de la botella que abraza el tope
SEGMENTOS = 180


def semieje(z, offset):
    a = np.interp(z / ALTO_MAX, *zip(*PERFIL))
    return a - offset, a * ANCHO_RELATIVO - offset


def cuerpo(offset=0.0, z0=0.0, altura=ALTO_MAX * 1.2):
    """Sólido ovalado; offset>0 lo encoge (para el hueco interior)."""
    Rh, Rv = RADIO_FONDO[0] - offset, RADIO_FONDO[1] - offset
    zs = list(z0 + Rv - Rv * np.cos(np.linspace(0, np.pi / 2, 32)))
    zs += list(np.linspace(z0 + Rv, altura, 30)[1:])
    t = np.linspace(0, 2 * np.pi, SEGMENTOS, endpoint=False)
    pts = []
    for z in zs:
        a, b = semieje(z, offset)
        dz = z - z0
        if dz < Rv:  # redondeo del fondo
            encoge = Rh * (1 - np.sqrt(max(1 - ((Rv - dz) / Rv) ** 2, 0.0)))
            a, b = a - encoge, b - encoge
        pts += [(a * np.cos(k), b * np.sin(k), z) for k in t]
    return solevado(np.array(pts), len(zs))


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
    for i in range(n):
        caras.append((abajo, (i + 1) % n, i))
        top = (n_anillos - 1) * n
        caras.append((arriba, top + i, top + (i + 1) % n))
    verts = np.vstack([pts, tapas]).astype(np.float32)
    return Manifold(Mesh(vert_properties=verts, tri_verts=np.array(caras, dtype=np.uint32)))


def plano_boca():
    """Pendiente y altura media del corte diagonal de la boca."""
    a_min, _ = semieje(ALTO_MIN, 0)
    a_max, _ = semieje(ALTO_MAX, 0)
    pendiente = (ALTO_MAX - ALTO_MIN) / (a_min + a_max)
    medio = ALTO_MIN + pendiente * a_min
    return pendiente, medio


def corte_diagonal(pendiente, medio):
    caja = Manifold.cube((1000, 1000, 1000), center=True).translate((0, 0, -500))
    ang = np.degrees(np.arctan(pendiente))
    return caja.rotate((0, -ang, 0)).translate((0, 0, medio))


def asa(pendiente, medio):
    """Ranura ovalada que atraviesa la pared alta bajo el borde."""
    x, z = centro_asa(pendiente, medio)
    rx = ASA[0] / 2 - ASA[1] / 2
    ranura = Manifold.batch_hull([
        Manifold.cylinder(60, ASA[1] / 2, ASA[1] / 2, 64, center=True)
        .rotate((0, 90, 0)).translate((0, y, 0)) for y in (-rx, rx)])
    return ranura.translate((x, 0, z))


def tope():
    """Calzo redondeado en el fondo; su cara hacia el lado alto es cóncava
    para que el culo de la botella encaje y la botella quede recostada."""
    x0, l, w, h = TOPE["x"], TOPE["largo"], TOPE["ancho"], TOPE["alto"]
    r = 4.0
    esferas = []
    for dx in (-l / 2 + r, l / 2 - r):
        for dy in (-w / 2 + r, w / 2 - r):
            esferas.append(Manifold.sphere(r, 32).translate((x0 + dx, dy, FONDO - r)))
    for dy in (-w / 2 + 2 * r, w / 2 - 2 * r):  # lomo superior, más alto hacia fuera
        esferas.append(Manifold.sphere(r, 32).translate((x0 - l / 4, dy, FONDO + h - r)))
    calzo = Manifold.batch_hull(esferas)
    botella = Manifold.cylinder(200, BOTELLA_D / 2, BOTELLA_D / 2, 128) \
        .translate((x0 + l / 2 - 6 + BOTELLA_D / 2, 0, FONDO + 1.5))
    return calzo - botella


def centro_asa(pendiente, medio):
    x = semieje(ALTO_MAX, 0)[0] - 6
    return x, medio + pendiente * x - ASA_BAJO_BORDE - ASA[1] / 2


def texto(pendiente, medio):
    """Letras en relieve envueltas sobre la pared alta, bajo el asa."""
    fuente = FontProperties(family="DejaVu Serif", weight="bold")
    ruta = TextPath((0, 0), TEXTO, size=1.0, prop=fuente)
    escala = LETRA / TextPath((0, 0), "J", size=1.0, prop=fuente).get_extents().height
    polis = [p * escala for p in ruta.to_polygons() if len(p) > 2]
    ext = ruta.get_extents()
    ancho = ext.width * escala
    letras = CrossSection(polis, FillRule.EvenOdd).translate((-ancho / 2 - ext.x0 * escala, 0))
    z_base = centro_asa(pendiente, medio)[1] - ASA[1] / 2 - TEXTO_BAJO_ASA - LETRA
    # u = recorrido sobre la pared, v = altura, w = hacia fuera de la pared
    placa = letras.extrude(RELIEVE + 2.0).translate((0, 0, -2.0)).refine_to_length(0.8)
    t = np.linspace(-np.pi / 2, np.pi / 2, 2001)

    def envolver(p):
        u, v, w = p
        z = z_base + v
        a, b = semieje(z, 0)
        # longitud de arco desde el extremo del óvalo (+x) hacia +y
        dx, dy = -a * np.sin(t), b * np.cos(t)
        s = np.concatenate([[0], np.cumsum(np.hypot(dx, dy)[1:] * np.diff(t))])
        s -= np.interp(0.0, t, s)
        k = np.interp(u, s, t)
        nx, ny = b * np.cos(k), a * np.sin(k)
        n = np.hypot(nx, ny)
        return (a * np.cos(k) + w * nx / n, b * np.sin(k) + w * ny / n, z)

    return placa.warp(envolver)


def construir():
    pendiente, medio = plano_boca()
    exterior = cuerpo() ^ corte_diagonal(pendiente, medio)
    interior = cuerpo(offset=PARED, z0=FONDO)
    solido = (exterior - interior - asa(pendiente, medio)) + (tope() ^ exterior)
    solido = solido + (texto(pendiente, medio) - interior)
    m = solido.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)


if __name__ == "__main__":
    malla = construir()
    malla.export("cubitera.stl")
    print("estanca:", malla.is_watertight, "| cuerpos:", malla.body_count,
          "| volumen cm3:", round(malla.volume / 1000, 1))
    print("tamaño mm:", np.round(malla.extents, 1))
