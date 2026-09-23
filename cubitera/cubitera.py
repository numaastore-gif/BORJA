"""Genera el STL de una cubitera para una botella de vino.

Silueta ajustada con curvas suaves a la foto de la cubitera transparente de
referencia y escalada a sus medidas (20 x 20,5 x 24 cm): se ensancha de forma
continua desde un fondo pequeño y redondeado hasta la boca, que está cortada
en curva (baja en un lado y alta en el del asa). El asa es una ranura
triangular redondeada y simétrica; debajo van el nombre y la fecha en relieve
siguiendo la pared, y en el fondo hay un tope para que la botella quede
recostada contra la pared alta.
Todas las medidas en mm.

    pip install numpy trimesh manifold3d matplotlib shapely fonttools
    python cubitera.py
"""
import pathlib

import numpy as np
import trimesh
from fontTools.ttLib import TTFont
from manifold3d import CrossSection, FillRule, JoinType, Manifold, Mesh, OpType
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from shapely.geometry import LineString, Polygon

# --- Parámetros -------------------------------------------------------------
# Semieje largo exterior según la altura: curva suave ajustada a la silueta
# calcada de la foto (error < 1 mm), a(z) = c0 + c1*z - c2*exp(-z/L).
# Al ser una sola función sin tramos, la pared no tiene pliegues.
PERFIL = dict(c0=76.456, c1=0.1166, c2=34.238, L=33.336)
# Borde de la boca: parábola ajustada al borde de la foto, z(x) = p0*x² + p1*x + p2.
BOCA = dict(p0=5.14e-4, p1=0.260454, p2=207.33)
ANCHO_RELATIVO = 20.5 / 20.0  # semieje transversal / semieje largo
PARED = 3.0
FONDO = 4.0
REDONDEO_FONDO = (8.0, 5.0)  # radio de la arista del fondo por fuera y por dentro
# Asa: ranura triangular redondeada y simétrica (base abajo, vértice arriba).
# (u, v, radio horizontal, radio vertical) de las elipses que la envuelven;
# u a lo largo de la pared (0 = punta del lado alto), v hacia arriba. El
# vértice es una elipse ancha para que el pico quede suave.
ASA = [(-44.0, 6.0, 6.0, 6.0), (44.0, 6.0, 6.0, 6.0), (0.0, 16.0, 22.0, 12.0)]
ASA_Z = 188.0          # altura del borde inferior de la ranura
# Texto en Playfair Display (la de numashome.com), centrado bajo el asa.
# Cada línea: tramos (texto, cursiva), altura de mayúscula, espaciado entre
# letras (fracción de la altura) y línea base.
LINEAS = [
    dict(tramos=[("Jose ", False), ("y", True), (" Valle", False)], letra=14.0, aire=0.0, z=166.0),
    dict(tramos=[("10/09/1994", False)], letra=8.5, aire=0.12, z=151.0),
]
FUENTES = {False: "PlayfairDisplay-Medium.ttf", True: "PlayfairDisplay-MediumItalic.ttf"}  # OFL
ENGROSAR = 0.15        # mm que se engordan los trazos finos para que se impriman
# Relieve en escalones que imitan un bisel: (ensanche del trazo, altura) en mm,
# así las letras nacen de la pared en vez de parecer pegadas.
RELIEVE = [(0.3, 0.4), (0.0, 0.8)]
TOPE = dict(x=-34.0, ancho=30.0, alto=16.0)  # suplemento del fondo
SEGMENTOS = 240
PASO_Z = 1.5           # separación entre anillos de la pared
ALTO_CUERPO = 290.0    # el cuerpo se genera algo más alto y la boca lo recorta


def perfil(z):
    p = PERFIL
    return p["c0"] + p["c1"] * z - p["c2"] * np.exp(-np.asarray(z) / p["L"])


def semieje(z, offset=0.0):
    a = perfil(z)
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


def contorno(interior=False):
    """Media sección del cuerpo (radio a, altura z) de abajo arriba, con la
    arista entre fondo y pared redondeada, muestreada cada PASO_Z mm."""
    zs = np.arange(0.0, ALTO_CUERPO + 1e-6, 0.25)
    a = perfil(zs)
    if interior:
        # desplaza la curva PARED mm en su normal
        pend = np.gradient(a, zs)
        n = np.hypot(1, pend)
        z_in, a_in = zs + PARED * pend / n, a - PARED / n
        zs = np.arange(FONDO, ALTO_CUERPO + 1e-6, 0.25)
        a = np.interp(zs, z_in, a_in)
    r = REDONDEO_FONDO[1 if interior else 0]
    # sección completa (simétrica) para que el redondeo solo afecte al fondo
    seccion = Polygon([*zip(-a[::-1], zs[::-1]), *zip(a, zs)])
    seccion = seccion.buffer(-r, quad_segs=32).buffer(r, quad_segs=32)
    x, z = np.array(seccion.exterior.coords).T
    x0 = x[(np.abs(z - zs[0]) < 1e-6)].max()
    lado = (x > 0) & (z > zs[0] + 1e-6) & (z < zs[-1] - 3 * r)
    orden = np.argsort(z[lado])
    linea = LineString(np.c_[x[lado][orden], z[lado][orden]])
    borde = [linea.interpolate(d) for d in np.arange(PASO_Z, linea.length, PASO_Z)]
    return [(x0, zs[0])] + [(p.x, p.y) for p in borde]


def cuerpo(interior=False):
    """Sólido exterior, o el hueco interior (pared de grosor constante)."""
    t = np.linspace(0, 2 * np.pi, SEGMENTOS, endpoint=False)
    anillos = contorno(interior)
    pts = [(ai * np.cos(k), ai * ANCHO_RELATIVO * np.sin(k), z)
           for ai, z in anillos for k in t]
    return solevado(np.array(pts), len(anillos))


def bajo_la_boca():
    """Todo lo que queda por debajo del borde curvo de la boca."""
    x = np.linspace(-150, 150, 301)
    z = BOCA["p0"] * x ** 2 + BOCA["p1"] * x + BOCA["p2"]
    contorno = [(-150.0, -50.0), (150.0, -50.0), *zip(x[::-1], z[::-1])]
    return (CrossSection([np.array(contorno)]).extrude(600)
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
    forma = CrossSection.batch_hull([CrossSection.circle(1.0, 96).scale((ru, rv)).translate((u, v))
                                     for u, v, ru, rv in ASA])
    return envolver(forma.extrude(16).translate((0, 0, -10)), ASA_Z)


def fichero(cursiva):
    return str(pathlib.Path(__file__).with_name(FUENTES[cursiva]))


def linea(tramos, letra, aire):
    """Contorno 2D de una línea de texto, centrado en u=0 y con base en v=0."""
    recta = FontProperties(fname=fichero(False))
    escala = letra / TextPath((0, 0), "J", size=1.0, prop=recta).get_extents().height
    polis, cursor = [], 0.0
    for tramo, cursiva in tramos:
        prop = FontProperties(fname=fichero(cursiva))
        fuente = TTFont(fichero(cursiva))
        cmap, hmtx, em = fuente.getBestCmap(), fuente["hmtx"], fuente["head"].unitsPerEm
        piezas = tramo if aire else [tramo]  # con espaciado, letra a letra
        for pieza in piezas:
            ruta = TextPath((cursor, 0), pieza, size=1.0, prop=prop)
            polis += [p * escala for p in ruta.to_polygons() if len(p) > 2]
            cursor += sum(hmtx[cmap[ord(ch)]][0] for ch in pieza) / em + aire * letra / escala
    letras = CrossSection(polis, FillRule.EvenOdd).offset(ENGROSAR, JoinType.Round)
    x0, _, x1, _ = letras.bounds()
    return letras.translate((-(x0 + x1) / 2, 0))


def texto():
    """Líneas en relieve biselado, enrolladas sobre la pared bajo el asa."""
    relieve = []
    for l in LINEAS:
        letras = linea(l["tramos"], l["letra"], l["aire"])
        for ensanche, alto in RELIEVE:
            capa = letras.offset(ensanche, JoinType.Round) if ensanche else letras
            relieve.append(envolver(capa.extrude(alto + 2.0).translate((0, 0, -2.0)), l["z"]))
    # sin detalles por debajo de 0,01 mm, que al guardar en STL se solaparían
    return Manifold.batch_boolean(relieve, OpType.Add).set_tolerance(0.01)


def tope():
    """Calzo en el fondo, pegado a la pared del lado bajo: una rampa
    redondeada que nace de la pared y muere en el suelo sin aristas, donde
    apoya el culo de la botella para que quede recostada contra la pared alta."""
    x0, w, h = TOPE["x"], TOPE["ancho"], TOPE["alto"]
    esferas = []
    for y in (-w / 2 + 6, w / 2 - 6):
        esferas.append(Manifold.sphere(6.0, 48).translate((x0 - 16, y, FONDO + 6.5)))  # dentro de la pared
        esferas.append(Manifold.sphere(5.0, 48).translate((x0 - 6, y * 0.85, FONDO + h - 5)))  # lomo
        esferas.append(Manifold.sphere(2.5, 32).translate((x0 + 7, y, FONDO)))        # pie en el suelo
    esferas.append(Manifold.sphere(2.5, 32).translate((x0 + 5, 0, FONDO)))  # pie algo cóncavo
    return Manifold.batch_hull(esferas)


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
