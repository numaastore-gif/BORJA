"""Lámpara «tronco en rodajas» para numashome.

Un tronco con corteza cortado en rodajas separadas por rendijas de luz:

  base      bloque macizo con el asiento del difusor, paso para el tubo
            roscado M10 del portalámparas, alojamiento de la tuerca por debajo,
            canal para el cable y «numa home» grabado en la cara inferior.
  rodajas   12 anillos de tronco. Cada uno baja por el difusor y se asienta
            solo en su escalón, así que las rendijas salen siempre iguales. Dos
            muescas a 0° y 150° encajan en las guías del difusor: solo entran
            en una posición y la corteza casa de una rodaja a la siguiente.
  remate    tapa superior cortada en bisel, con los anillos de crecimiento
            grabados en el corte; se encaja sobre el extremo del difusor.
  difusor   tubo escalonado translúcido (un escalón cónico a 45° por rodaja,
            que centra cada pieza), con las dos guías y una pestaña que se
            encaja en la base.

Todas las piezas salen del mismo tronco, así que la corteza continúa de una
pieza a la siguiente. Corteza con vetas verticales y grietas, y anillos de
crecimiento grabados en las caras de corte que se ven por las rendijas.
Medidas en mm.

    pip install numpy trimesh manifold3d matplotlib fonttools
    python lampara.py
"""
import pathlib

import numpy as np
import trimesh
from fontTools.ttLib import TTFont
from manifold3d import CrossSection, FillRule, Manifold, Mesh
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

AQUI = pathlib.Path(__file__).parent

# --- Tronco --------------------------------------------------------------------
RADIO = 62.0            # radio medio del tronco (Ø 124 mm)
SEGMENTOS = 360         # puntos por vuelta (1 por grado)
PASO_Z = 1.0            # separación entre anillos de la malla
SEMILLA = 7             # cambia la corteza y los anillos

# --- Alturas -----------------------------------------------------------------------
ALTO_BASE = 50.0
RODAJAS = 12
GROSOR_RODAJA = 7.0
RENDIJA = 5.0           # hueco de luz entre piezas
ALTO_REMATE = 50.0      # altura media del remate por encima de su base
BISEL = 14.0            # grados de inclinación del corte superior

# --- Difusor ----------------------------------------------------------------------
R_DIFUSOR = 38.0        # radio exterior en la base (Ø 76 mm)
ESCALON = 1.0           # lo que se estrecha en cada nivel
PARED_DIFUSOR = 1.6
GUIAS = (0.0, 150.0)    # ángulos de las guías (asimétricas: una sola posición)
GUIA = dict(ancho=4.0, alto=2.0)
PESTANA = dict(radio=R_DIFUSOR + 4.0, grosor=3.0, lengueta=4.0)  # encaje en la base
HOLGURA = 0.2           # holgura de deslizamiento de rodajas y remate
ENTRA_EN_REMATE = 18.0  # lo que el difusor entra en el remate

# --- Electricidad ------------------------------------------------------------------
TUBO_M10 = 10.5         # paso del tubo roscado M10x1 del portalámparas
TUERCA = dict(diametro=26.0, alto=8.0)   # alojamiento de tuerca y arandela
CABLE = dict(ancho=7.0, alto=5.0, angulo=180.0)  # canal del cable (sale por detrás)

# --- Acabados -----------------------------------------------------------------------
ANILLOS = dict(profundidad=0.4, ancho=0.6, separacion=5.5)
TEXTO = "numa home"
TEXTO_ALTO = 7.0
TEXTO_HONDO = 0.6

Z_RODAJA = [ALTO_BASE + RENDIJA + i * (GROSOR_RODAJA + RENDIJA) for i in range(RODAJAS)]
Z_REMATE = Z_RODAJA[-1] + GROSOR_RODAJA + RENDIJA
Z_TOPE = Z_REMATE + ALTO_REMATE + np.tan(np.radians(BISEL)) * RADIO * 1.3


# --- Forma del tronco -----------------------------------------------------------------
rng = np.random.default_rng(SEMILLA)
LOBULOS = [(n, a, rng.uniform(0, 2 * np.pi), rng.uniform(-0.006, 0.006))
           for n, a in ((2, 0.055), (3, 0.035), (4, 0.018), (5, 0.012), (7, 0.006))]
VETAS = [(int(rng.integers(18, 70)), rng.uniform(0.12, 0.28), rng.uniform(0, 2 * np.pi),
          rng.uniform(-0.05, 0.05)) for _ in range(10)]
GRIETAS = [(int(rng.integers(9, 20)), rng.uniform(0.9, 1.6), rng.uniform(0, 2 * np.pi),
            rng.uniform(-0.02, 0.02)) for _ in range(4)]


def centro(z):
    """El tronco no es recto: su eje se desvía unos milímetros."""
    return 3.0 * np.sin(z / 95.0), 2.0 * np.cos(z / 130.0) - 2.0


def radio_liso(theta, z):
    r = np.ones_like(theta)
    for n, a, fase, giro in LOBULOS:
        r += a * np.cos(n * theta + fase + giro * z)
    return RADIO * r * (1 - 0.0003 * z)


def corteza(theta, z):
    """Relieve de la corteza: vetas verticales onduladas y grietas estrechas."""
    d = np.zeros_like(theta)
    for n, a, fase, b in VETAS:
        d += a * np.sin(n * theta + b * z + fase)
    for n, a, fase, b in GRIETAS:
        d -= a * (0.5 + 0.5 * np.sin(n * theta + b * z + fase)) ** 14
    return d


def tronco():
    zs = np.arange(0.0, Z_TOPE + PASO_Z, PASO_Z)
    t = np.linspace(0, 2 * np.pi, SEGMENTOS, endpoint=False)
    pts = []
    for z in zs:
        cx, cy = centro(z)
        r = radio_liso(t, z) + corteza(t, z)
        pts.append(np.c_[cx + r * np.cos(t), cy + r * np.sin(t), np.full_like(t, z)])
    pts = np.vstack(pts)
    n, filas = SEGMENTOS, len(zs)
    caras = []
    for f in range(filas - 1):
        a = f * n + np.arange(n)
        b = f * n + (np.arange(n) + 1) % n
        caras += list(np.c_[a, b, b + n]) + list(np.c_[a, b + n, a + n])
    abajo, arriba = len(pts), len(pts) + 1
    tapas = np.array([[*centro(0.0), 0.0], [*centro(zs[-1]), zs[-1]]])
    top = (filas - 1) * n
    for i in range(n):
        caras.append((abajo, (i + 1) % n, i))
        caras.append((arriba, top + i, top + (i + 1) % n))
    verts = np.vstack([pts, tapas]).astype(np.float32)
    return Manifold(Mesh(vert_properties=verts, tri_verts=np.array(caras, dtype=np.uint32)))


def corte_superior():
    """Semiespacio por debajo del plano inclinado del corte de arriba."""
    z_medio = Z_REMATE + ALTO_REMATE
    caja = Manifold.cube((1000, 1000, 1000), center=True).translate((0, 0, -500))
    return caja.rotate((0, BISEL, 0)).translate((*centro(z_medio), z_medio))


def franja(z0, z1):
    return Manifold.cube((400, 400, z1 - z0)).translate((-200, -200, z0))


# --- Anillos de crecimiento --------------------------------------------------------------
def anillos(z, r_min):
    """Surcos concéntricos que siguen la forma del tronco a la altura z, desde
    el borde (dejando la corteza) hasta r_min."""
    t = np.linspace(0, 2 * np.pi, SEGMENTOS, endpoint=False)
    cx, cy = centro(z)
    base = radio_liso(t, z)
    rr = np.random.default_rng(int(z * 10) + SEMILLA)
    surcos = []
    k = 3.5  # primer anillo, dentro de la corteza
    while True:
        r = base - k + 0.35 * np.sin(rr.integers(3, 9) * t + rr.uniform(0, 6.3))
        if r.min() < r_min:
            break
        fuera = np.c_[cx + r * np.cos(t), cy + r * np.sin(t)]
        r2 = r - ANILLOS["ancho"]
        dentro = np.c_[cx + r2 * np.cos(t), cy + r2 * np.sin(t)]
        surcos.append(CrossSection([fuera]) - CrossSection([dentro]))
        k += ANILLOS["separacion"] * rr.uniform(0.7, 1.3)
    return CrossSection.compose(surcos) if surcos else CrossSection()


def grabar_anillos_arriba(pieza, z, r_min):
    h = ANILLOS["profundidad"]
    return pieza - anillos(z, r_min).extrude(h + 1).translate((0, 0, z - h))


# --- Difusor --------------------------------------------------------------------------------
def radio_nivel(i):
    """Radio exterior del difusor en el nivel i (-1 = por debajo de la primera rodaja)."""
    return R_DIFUSOR - (i + 1) * ESCALON


def perfil_difusor(extra=0.0):
    """(z, radio) del escalonado: cada pieza se asienta en un cono a 45° que
    termina justo a su altura (restando la holgura)."""
    z_ini = ALTO_BASE - PESTANA["grosor"]
    pts = [(z_ini, radio_nivel(-1) + extra)]
    for i, z in enumerate(Z_RODAJA + [Z_REMATE]):
        pts += [(z - ESCALON + HOLGURA, radio_nivel(i - 1) + extra), (z + HOLGURA, radio_nivel(i) + extra)]
    pts.append((Z_REMATE + ENTRA_EN_REMATE, radio_nivel(RODAJAS) + extra))
    return pts


def solido_revolucion(perfil, segmentos=180):
    zs, rs = zip(*perfil)
    t = np.linspace(0, 2 * np.pi, segmentos, endpoint=False)
    pts = np.vstack([np.c_[r * np.cos(t), r * np.sin(t), np.full_like(t, z)] for z, r in perfil])
    n, filas = segmentos, len(perfil)
    caras = []
    for f in range(filas - 1):
        a = f * n + np.arange(n)
        b = f * n + (np.arange(n) + 1) % n
        caras += list(np.c_[a, b, b + n]) + list(np.c_[a, b + n, a + n])
    abajo, arriba = len(pts), len(pts) + 1
    tapas = np.array([[0, 0, zs[0]], [0, 0, zs[-1]]])
    top = (filas - 1) * n
    for i in range(n):
        caras.append((abajo, (i + 1) % n, i))
        caras.append((arriba, top + i, top + (i + 1) % n))
    verts = np.vstack([pts, tapas]).astype(np.float32)
    return Manifold(Mesh(vert_properties=verts, tri_verts=np.array(caras, dtype=np.uint32)))


def guias(extra_radio=0.0, extra_ancho=0.0):
    """Las dos guías verticales, siguiendo el escalonado del difusor."""
    alto = GUIA["alto"] + extra_radio
    ancho = GUIA["ancho"] + extra_ancho
    perfil = perfil_difusor()
    zs = [z for z, _ in perfil]
    piezas = []
    for ang in GUIAS:
        tramos = []
        for (z0, r0), (z1, r1) in zip(perfil, perfil[1:]):
            if z1 - z0 < 1e-6:
                continue
            caja = lambda r, z: [(r - 1.0, -ancho / 2, z), (r + alto, -ancho / 2, z),
                                 (r + alto, ancho / 2, z), (r - 1.0, ancho / 2, z)]
            tramos.append(Manifold.hull_points(np.array(caja(r0, z0) + caja(r1, z1))))
        piezas.append(Manifold.compose(tramos).rotate((0, 0, ang)))
    return Manifold.compose(piezas)


def difusor():
    fuera = solido_revolucion(perfil_difusor())
    dentro = solido_revolucion([(z, r - PARED_DIFUSOR) for z, r in perfil_difusor()])
    dentro = dentro + Manifold.cylinder(1, R_DIFUSOR - PARED_DIFUSOR, R_DIFUSOR - PARED_DIFUSOR, 180) \
        .translate((0, 0, ALTO_BASE - PESTANA["grosor"] - 0.5))
    z0 = ALTO_BASE - PESTANA["grosor"]
    pestana = Manifold.cylinder(PESTANA["grosor"], PESTANA["radio"], PESTANA["radio"], 180) \
        .translate((0, 0, z0))
    for ang in GUIAS:  # lengüetas que fijan la orientación del difusor en la base
        pestana = pestana + Manifold.cube((PESTANA["lengueta"] + 1, 6.0, PESTANA["grosor"])) \
            .translate((PESTANA["radio"] - 1, -3.0, z0)).rotate((0, 0, ang))
    guia = guias()
    return (fuera + pestana + guia) - dentro


def hueco_para(nivel, z0, z1):
    """Agujero de una pieza para el nivel dado del difusor, con las muescas
    de las guías (holgura de deslizamiento incluida)."""
    r = radio_nivel(nivel) + HOLGURA
    h = z1 - z0 + 2
    agujero = Manifold.cylinder(h, r, r, 180)
    for ang in GUIAS:
        agujero = agujero + Manifold.cube((GUIA["alto"] + 1.0 + HOLGURA, GUIA["ancho"] + 2 * HOLGURA, h)) \
            .translate((r - 1.0, -(GUIA["ancho"] + 2 * HOLGURA) / 2, 0)).rotate((0, 0, ang))
    return agujero.translate((0, 0, z0 - 1))


# --- Texto de la base ------------------------------------------------------------------------
def texto_inferior():
    fichero = str(AQUI / "PlayfairDisplay-Medium.ttf")
    prop = FontProperties(fname=fichero)
    ruta = TextPath((0, 0), TEXTO, size=1.0, prop=prop)
    escala = TEXTO_ALTO / TextPath((0, 0), "h", size=1.0, prop=prop).get_extents().height
    polis = [p * escala for p in ruta.to_polygons() if len(p) > 2]
    letras = CrossSection(polis, FillRule.EvenOdd)
    x0, y0, x1, y1 = letras.bounds()
    # se lee desde abajo: se refleja y se coloca delante (lejos del canal del cable)
    letras = letras.translate((-(x0 + x1) / 2, -(y0 + y1) / 2)).mirror((1, 0)).translate((0, -38.0))
    return letras.extrude(TEXTO_HONDO + 1).translate((0, 0, -1))


# --- Piezas ------------------------------------------------------------------------------------
def construir():
    log = tronco() ^ corte_superior()

    # base
    base = log ^ franja(0, ALTO_BASE)
    asiento = Manifold.cylinder(PESTANA["grosor"] + 1, PESTANA["radio"] + HOLGURA, PESTANA["radio"] + HOLGURA, 180)
    for ang in GUIAS:
        asiento = asiento + Manifold.cube((PESTANA["lengueta"] + 1 + HOLGURA, 6.0 + 2 * HOLGURA, PESTANA["grosor"] + 1)) \
            .translate((PESTANA["radio"] - 1, -3.0 - HOLGURA, 0)).rotate((0, 0, ang))
    base = base - asiento.translate((0, 0, ALTO_BASE - PESTANA["grosor"]))
    base = base - Manifold.cylinder(ALTO_BASE + 2, TUBO_M10 / 2, TUBO_M10 / 2, 48).translate((0, 0, -1))
    base = base - Manifold.cylinder(TUERCA["alto"] + 1, TUERCA["diametro"] / 2, TUERCA["diametro"] / 2, 96) \
        .translate((0, 0, -1))
    canal = Manifold.cube((RADIO * 1.5, CABLE["ancho"], CABLE["alto"] + 1)) \
        .translate((0, -CABLE["ancho"] / 2, -1)).rotate((0, 0, CABLE["angulo"]))
    base = base - canal - texto_inferior()
    base = grabar_anillos_arriba(base, ALTO_BASE, PESTANA["radio"] + 4)

    # rodajas
    rodajas = []
    for i, z in enumerate(Z_RODAJA):
        r = log ^ franja(z, z + GROSOR_RODAJA)
        r = r - hueco_para(i, z, z + GROSOR_RODAJA)
        r = grabar_anillos_arriba(r, z + GROSOR_RODAJA, radio_nivel(i) + GUIA["alto"] + 5)
        rodajas.append(r)

    # remate: se asienta en el último escalón y cubre el extremo del difusor
    remate = log ^ franja(Z_REMATE, Z_TOPE + 10)
    remate = remate - hueco_para(RODAJAS, Z_REMATE, Z_REMATE + ENTRA_EN_REMATE + 0.5)
    h = ANILLOS["profundidad"]
    plano = corte_superior()
    surcos = anillos(Z_REMATE + ALTO_REMATE, 6.0).extrude(200).translate((0, 0, Z_REMATE))
    remate = remate - (surcos ^ plano - plano.translate((0, 0, -h / np.cos(np.radians(BISEL)))))

    return dict(base=base, rodajas=rodajas, remate=remate, difusor=difusor())


def a_trimesh(m):
    s = m.to_mesh()
    return trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)


if __name__ == "__main__":
    p = construir()
    todas = [("base", p["base"]), ("remate", p["remate"]), ("difusor", p["difusor"])] + \
        [(f"rodaja_{i + 1:02d}", r) for i, r in enumerate(p["rodajas"])]
    for nombre, m in todas:
        t = a_trimesh(m)
        t.export(AQUI / f"{nombre}.stl")
        print(f"{nombre:10s} estanca={t.is_watertight} tamaño={np.round(t.extents, 1)} "
              f"volumen={t.volume / 1000:.0f} cm3")
