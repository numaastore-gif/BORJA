"""Lámpara de madera en rodajas para numashome, con la forma de la lámpara
clara de la referencia: un tronco con la base alta y ensanchada como el pie de
un árbol (con pliegues verticales hondos), una zona central de rodajas finas
algo más estrecha que se curva en S, y un remate alto y más ancho cortado en
un bisel suave, un poco inclinado hacia un lado:

  base      bloque macizo con el asiento del difusor, paso para el tubo
            roscado M10 del portalámparas, alojamiento de la tuerca por debajo,
            canal para el cable y «numa home» grabado en la cara inferior.
  rodajas   12 piezas. Cada una baja por el difusor y se asienta sola en su
            escalón, así que las rendijas salen iguales. Dos muescas a 0° y
            150° encajan en las guías del difusor: solo entran en una posición.
  remate    tapa superior cortada en bisel que cubre el extremo del difusor.
  difusor   tubo escalonado translúcido con un escalón cónico a 45° por pieza,
            las dos guías y una pestaña que se encaja en la base.

Textura: la de la lámpara de referencia. textura_corteza.npy es el relieve
de la corteza escaneado de su STL (60 × 42 mm a 0,3 mm/px, sin la forma
general); con sus zonas limpias se compone una baldosa que se repite sin
costuras y se aplica como relieve real en todas las caras laterales, más
grietas estrechas y profundas como las de la referencia. Las caras de corte
son lisas, como en la referencia. Medidas en mm.

    pip install numpy trimesh manifold3d matplotlib fonttools opencv-python-headless
    python lampara.py            # piezas para imprimir (resolución 0,4 mm)
    python lampara.py --vista    # versión ligera para el visor
"""
import pathlib
import sys

import cv2
import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, Manifold, Mesh, OpType, triangulate
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

AQUI = pathlib.Path(__file__).parent
VISTA = "--vista" in sys.argv
RESOLUCION = 0.8 if VISTA else 0.4  # separación de puntos en las caras con textura
SEMILLA = 11

# --- Forma (proporciones de la lámpara clara de la foto) ------------------------------
# Radio medio del tronco según la altura (z, radio): pie ensanchado, cintura en
# las rodajas y remate algo más ancho.
PERFIL = [(0, 63.0), (12, 59.0), (35, 56.5), (70, 55.5), (95, 54.5), (110, 51.5),
          (150, 50.0), (185, 51.5), (205, 55.0), (215, 57.5), (250, 58.0), (300, 57.0)]
# Desplazamiento del eje (z, x, y): las rodajas se curvan en S y el remate se
# inclina hacia un lado.
EJE = [(0, 0.0, 0.0), (95, 0.0, 0.0), (140, 5.0, 1.0), (185, 2.0, -1.0), (215, -2.0, 0.0), (300, -5.0, 0.0)]
LOBULOS = [(2, 0.045), (3, 0.03), (5, 0.012), (7, 0.006)]  # (número, amplitud relativa)
PLIEGUES = dict(cantidad=8, hondo=7.0, ancho=(7.0, 12.0), alto=95.0)  # pliegues del pie
DESORDEN = dict(giro=2.0, desplazamiento=0.8)  # cada rodaja, apenas descolocada

# --- Alturas -----------------------------------------------------------------------------
ALTO_BASE = 90.0
RODAJAS = 12
GROSOR_RODAJA = 6.3     # como las rodajas de la referencia
RENDIJA = 3.0
ALTO_REMATE = 60.0
BISEL = 8.0

# --- Textura -------------------------------------------------------------------------
TEXTURA = AQUI / "textura_corteza.npy"
PIXEL = 0.3             # mm por píxel de la textura escaneada
GRIETAS_POR_CM2 = 0.07  # densidad de grietas
GRIETA = dict(largo=(14.0, 38.0), ancho=(1.2, 2.4), hondo=(1.2, 2.2), inclinacion=0.18)

# --- Difusor -------------------------------------------------------------------------
R_DIFUSOR = 38.0
ESCALON = 1.0
PARED_DIFUSOR = 1.6
GUIAS = (0.0, 150.0)
GUIA = dict(ancho=4.0, alto=2.0)
PESTANA = dict(radio=R_DIFUSOR + 4.0, grosor=3.0, lengueta=4.0)
HOLGURA = 0.2
ENTRA_EN_REMATE = 18.0

# --- Electricidad y rótulo -------------------------------------------------------------
TUBO_M10 = 10.5
TUERCA = dict(diametro=26.0, alto=8.0)
CABLE = dict(ancho=7.0, alto=5.0, angulo=180.0)
TEXTO = "numa home"
TEXTO_ALTO = 7.0
TEXTO_HONDO = 0.6

Z_RODAJA = [ALTO_BASE + RENDIJA + i * (GROSOR_RODAJA + RENDIJA) for i in range(RODAJAS)]
Z_REMATE = Z_RODAJA[-1] + GROSOR_RODAJA + RENDIJA
ALTO_TOTAL = Z_REMATE + ALTO_REMATE
Z_TOPE = ALTO_TOTAL + np.tan(np.radians(BISEL)) * 75

rng = np.random.default_rng(SEMILLA)


# --- Contorno orgánico ---------------------------------------------------------------------
LOBULO_FASE = [(n, a, rng.uniform(0, 2 * np.pi), rng.uniform(-0.004, 0.004)) for n, a in LOBULOS]
PLIEGUE = [(rng.uniform(0, 2 * np.pi), rng.uniform(*PLIEGUES["ancho"]), rng.uniform(0.6, 1.0))
           for _ in range(PLIEGUES["cantidad"])]
R_MEDIO = 55.0
PERIMETRO = 2 * np.pi * R_MEDIO
ANGULOS = np.linspace(0, 2 * np.pi, int(PERIMETRO / RESOLUCION), endpoint=False)
ARCO = ANGULOS * R_MEDIO  # coordenada horizontal de la textura (mm)


def eje(z):
    zs, xs, ys = zip(*EJE)
    return np.interp(z, zs, xs), np.interp(z, zs, ys)


def radio(theta, z):
    r = np.full_like(theta, np.interp(z, *zip(*PERFIL)))
    for n, a, fase, giro in LOBULO_FASE:
        r *= 1 + a * np.cos(n * theta + fase + giro * z)
    # pliegues verticales del pie: surcos anchos que se desvanecen hacia arriba
    fuerza = np.clip(1 - z / PLIEGUES["alto"], 0, 1) ** 1.5
    for ang, ancho, k in PLIEGUE:
        d = (theta - ang + np.pi) % (2 * np.pi) - np.pi
        r -= PLIEGUES["hondo"] * k * fuerza * np.exp(-0.5 * (d * np.interp(z, *zip(*PERFIL)) / (ancho / 2)) ** 2)
    return r


def normales(pts):
    """Normal hacia fuera de un contorno antihorario."""
    t = np.roll(pts, -1, axis=0) - np.roll(pts, 1, axis=0)
    n = np.c_[t[:, 1], -t[:, 0]]
    return n / np.linalg.norm(n, axis=1)[:, None]


# --- Textura -----------------------------------------------------------------------------------
def baldosa():
    """Baldosa periódica hecha con las zonas limpias del escaneo (sin la
    grieta y sus halos), empalmadas con fundidos."""
    d = np.load(TEXTURA)
    a, b = d[:, 5:70], d[:, 145:198]
    f = 10
    w = np.linspace(0, 1, f)[None, :]
    t = np.hstack([a[:, :-f], a[:, -f:] * (1 - w) + b[:, :f] * w, b[:, f:]])
    # periódica en horizontal y en vertical
    f = 14
    w = np.linspace(0, 1, f)[None, :]
    t = np.hstack([t[:, f:-f], t[:, -f:] * (1 - w) + t[:, :f] * w])
    w = np.linspace(0, 1, f)[:, None]
    t = np.vstack([t[f:-f], t[-f:] * (1 - w) + t[:f] * w])
    return (t - t.mean()).astype(np.float32)


BALDOSA = baldosa()


def veta(u, v):
    """Relieve de la veta en (u, v) mm, con interpolación bilineal periódica."""
    alto, ancho = BALDOSA.shape
    x, y = u / PIXEL, v / PIXEL
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    x0 %= ancho
    y0 %= alto
    x1, y1 = (x0 + 1) % ancho, (y0 + 1) % alto
    b = BALDOSA
    return (b[y0, x0] * (1 - fx) * (1 - fy) + b[y0, x1] * fx * (1 - fy)
            + b[y1, x0] * (1 - fx) * fy + b[y1, x1] * fx * fy)


def lista_grietas(v0, v1, semilla):
    r = np.random.default_rng(semilla)
    area = PERIMETRO * (v1 - v0) / 100.0
    g = []
    for _ in range(r.poisson(max(area * GRIETAS_POR_CM2, 0.3))):
        largo = r.uniform(*GRIETA["largo"])
        g.append(dict(u=r.uniform(0, PERIMETRO), v=r.uniform(v0 - largo * 0.6, v1 + largo * 0.2),
                      largo=largo, ancho=r.uniform(*GRIETA["ancho"]), hondo=r.uniform(*GRIETA["hondo"]),
                      incl=r.uniform(-1, 1) * GRIETA["inclinacion"], hacia_arriba=r.random() < 0.5))
    return g


def grietas(u, v, lista):
    """Hendiduras en V que se afinan hacia un extremo, como las de la referencia."""
    total = np.zeros_like(u)
    for g in lista:
        du = (u - g["u"] + PERIMETRO / 2) % PERIMETRO - PERIMETRO / 2
        t = (v - g["v"]) / g["largo"]
        if not g["hacia_arriba"]:
            t = 1 - t
        dentro = (t >= 0) & (t <= 1)
        eje = g["incl"] * (v - g["v"])
        ancho = g["ancho"] * np.sqrt(np.clip(1 - t, 0, 1)) * np.clip(t * 6, 0, 1)
        perfil = np.clip(1 - np.abs(du - eje) / np.maximum(ancho, 1e-3), 0, 1)
        total -= np.where(dentro, g["hondo"] * perfil * np.sqrt(np.clip(1 - t, 0, 1)), 0)
    return total


# --- Sólidos con textura -------------------------------------------------------------------------
def bloque(z0, z1, semilla, giro_extra=0.0, desplazamiento=(0.0, 0.0)):
    """Tramo del tronco entre z0 y z1 con la textura aplicada en el lateral.
    giro_extra (grados) y desplazamiento (mm) descolocan un poco la pieza."""
    filas = max(int(np.ceil((z1 - z0) / RESOLUCION)), 1)
    zs = np.linspace(z0, z1, filas + 1)
    lista = lista_grietas(z0, z1, semilla)
    ge = np.radians(giro_extra)
    anillos = []
    for z in zs:
        cx, cy = eje(z)
        r = radio(ANGULOS - ge, z)
        p = np.c_[cx + desplazamiento[0] + r * np.cos(ANGULOS), cy + desplazamiento[1] + r * np.sin(ANGULOS)]
        d = veta(ARCO, z) + grietas(ARCO, np.full_like(ARCO, z), lista)
        anillos.append(p + normales(p) * d[:, None])
    k = len(ANGULOS)
    pts = np.vstack([np.c_[a, np.full(k, z)] for a, z in zip(anillos, zs)])
    caras = []
    for f in range(len(zs) - 1):
        a = f * k + np.arange(k)
        b = f * k + (np.arange(k) + 1) % k
        caras.append(np.c_[a, b, b + k])
        caras.append(np.c_[a, b + k, a + k])
    abajo = triangulate([anillos[0]])[:, ::-1]
    arriba = triangulate([anillos[-1]]) + (len(zs) - 1) * k
    caras = np.vstack(caras + [abajo, arriba])
    return Manifold(Mesh(vert_properties=pts.astype(np.float32), tri_verts=caras.astype(np.uint32)))


def corte_superior():
    caja = Manifold.cube((1000, 1000, 1000), center=True).translate((0, 0, -500))
    # sube hacia +x: el lado alto del corte, como en la foto
    return caja.rotate((0, -BISEL, 0)).translate((*eje(ALTO_TOTAL), ALTO_TOTAL))


# --- Difusor ---------------------------------------------------------------------------------------
def radio_nivel(i):
    return R_DIFUSOR - (i + 1) * ESCALON


def perfil_difusor():
    pts = [(ALTO_BASE - PESTANA["grosor"], radio_nivel(-1))]
    for i, z in enumerate(Z_RODAJA + [Z_REMATE]):
        pts += [(z - ESCALON + HOLGURA, radio_nivel(i - 1)), (z + HOLGURA, radio_nivel(i))]
    pts.append((Z_REMATE + ENTRA_EN_REMATE, radio_nivel(RODAJAS)))
    return pts


def revolucion(perfil, segmentos=180, resalte=None):
    """Sólido de revolución del perfil (z, radio). «resalte» = lista de
    (ángulo en grados, ancho en mm, alto en mm): salientes verticales que forman
    parte del mismo contorno (las guías), sin uniones booleanas."""
    # columnas (ángulo, saliente): en cada borde de guía hay dos columnas al
    # mismo ángulo (pie y cara), en el orden en que se recorre el contorno
    columnas = []
    tramos = sorted(resalte or [])
    r0 = perfil[0][1]
    for a in np.linspace(0, 360, segmentos, endpoint=False):
        if not any(abs((a - g + 180) % 360 - 180) <= np.degrees(np.arcsin(w / 2 / r0)) + 0.5
                   for g, w, _ in tramos):
            columnas.append((a, 0.0))
    for g, w, alto in tramos:
        m = np.degrees(np.arcsin(w / 2 / r0))
        columnas += [(g - m, 0.0, 0), (g - m, alto, 1), (g, alto, 2), (g + m, alto, 3), (g + m, 0.0, 4)]
    columnas = [c if len(c) == 3 else (c[0], c[1], 0) for c in columnas]
    columnas.sort(key=lambda c: (c[0] % 360, c[2]))
    t = np.radians([c[0] for c in columnas])
    extra = np.array([c[1] for c in columnas])
    pts = np.vstack([np.c_[(r + extra) * np.cos(t), (r + extra) * np.sin(t), np.full_like(t, z)] for z, r in perfil])
    n, filas = len(columnas), len(perfil)
    caras = []
    for f in range(filas - 1):
        a = f * n + np.arange(n)
        b = f * n + (np.arange(n) + 1) % n
        caras += [np.c_[a, b, b + n], np.c_[a, b + n, a + n]]
    abajo, arriba = len(pts), len(pts) + 1
    tapas = np.array([[0, 0, perfil[0][0]], [0, 0, perfil[-1][0]]])
    top = (filas - 1) * n
    i = np.arange(n)
    caras += [np.c_[np.full(n, abajo), (i + 1) % n, i], np.c_[np.full(n, arriba), top + i, top + (i + 1) % n]]
    verts = np.vstack([pts, tapas]).astype(np.float32)
    return Manifold(Mesh(vert_properties=verts, tri_verts=np.vstack(caras).astype(np.uint32)))


def difusor():
    fuera = revolucion(perfil_difusor(), resalte=[(a, GUIA["ancho"], GUIA["alto"]) for a in GUIAS])
    # el hueco sobresale 1 mm por abajo y por arriba: tubo abierto en los dos
    # extremos y sin tapas coincidentes (darían aristas defectuosas)
    interior = [(z, r - PARED_DIFUSOR) for z, r in perfil_difusor()]
    interior = [(interior[0][0] - 1, interior[0][1])] + interior + [(interior[-1][0] + 1, interior[-1][1])]
    dentro = revolucion(interior)
    z0 = ALTO_BASE - PESTANA["grosor"]
    pestana = Manifold.cylinder(PESTANA["grosor"], PESTANA["radio"], PESTANA["radio"], 180).translate((0, 0, z0))
    for ang in GUIAS:
        pestana = pestana + Manifold.cube((PESTANA["lengueta"] + 1, 6.0, PESTANA["grosor"])) \
            .translate((PESTANA["radio"] - 1, -3.0, z0)).rotate((0, 0, ang))
    return (fuera + pestana) - dentro


def hueco_para(nivel, z0, z1):
    r = radio_nivel(nivel) + HOLGURA
    h = z1 - z0 + 2
    agujero = Manifold.cylinder(h, r, r, 180)
    for ang in GUIAS:
        agujero = agujero + Manifold.cube((GUIA["alto"] + 1.0 + HOLGURA, GUIA["ancho"] + 2 * HOLGURA, h)) \
            .translate((r - 1.0, -(GUIA["ancho"] + 2 * HOLGURA) / 2, 0)).rotate((0, 0, ang))
    return agujero.translate((0, 0, z0 - 1))


def texto_inferior():
    prop = FontProperties(fname=str(AQUI / "PlayfairDisplay-Medium.ttf"))
    ruta = TextPath((0, 0), TEXTO, size=1.0, prop=prop)
    escala = TEXTO_ALTO / TextPath((0, 0), "h", size=1.0, prop=prop).get_extents().height
    letras = CrossSection([p * escala for p in ruta.to_polygons() if len(p) > 2], FillRule.EvenOdd)
    x0, y0, x1, y1 = letras.bounds()
    letras = letras.translate((-(x0 + x1) / 2, -(y0 + y1) / 2)).mirror((1, 0)).translate((0, -32.0))
    return letras.extrude(TEXTO_HONDO + 1).translate((0, 0, -1))


# --- Piezas ------------------------------------------------------------------------------------------
def construir():
    base = bloque(0, ALTO_BASE, SEMILLA)
    asiento = Manifold.cylinder(PESTANA["grosor"] + 1, PESTANA["radio"] + HOLGURA, PESTANA["radio"] + HOLGURA, 180)
    for ang in GUIAS:
        asiento = asiento + Manifold.cube((PESTANA["lengueta"] + 1 + HOLGURA, 6.0 + 2 * HOLGURA, PESTANA["grosor"] + 1)) \
            .translate((PESTANA["radio"] - 1, -3.0 - HOLGURA, 0)).rotate((0, 0, ang))
    base = base - asiento.translate((0, 0, ALTO_BASE - PESTANA["grosor"]))
    base = base - Manifold.cylinder(ALTO_BASE + 2, TUBO_M10 / 2, TUBO_M10 / 2, 48).translate((0, 0, -1))
    base = base - Manifold.cylinder(TUERCA["alto"] + 1, TUERCA["diametro"] / 2, TUERCA["diametro"] / 2, 96) \
        .translate((0, 0, -1))
    canal = Manifold.cube((100, CABLE["ancho"], CABLE["alto"] + 1)).translate((0, -CABLE["ancho"] / 2, -1)) \
        .rotate((0, 0, CABLE["angulo"]))
    base = base - canal - texto_inferior()

    rodajas = []
    desorden = np.random.default_rng(SEMILLA + 500)
    for i, z in enumerate(Z_RODAJA):
        giro = desorden.uniform(-1, 1) * DESORDEN["giro"]
        ang = desorden.uniform(0, 2 * np.pi)
        desp = DESORDEN["desplazamiento"] * desorden.uniform(0.3, 1) * np.array([np.cos(ang), np.sin(ang)])
        r = bloque(z, z + GROSOR_RODAJA, SEMILLA + 1 + i, giro, desp) - hueco_para(i, z, z + GROSOR_RODAJA)
        rodajas.append(r)

    remate = bloque(Z_REMATE, Z_TOPE, SEMILLA + 99) ^ corte_superior()
    remate = remate - hueco_para(RODAJAS, Z_REMATE, Z_REMATE + ENTRA_EN_REMATE + 0.5)
    return dict(base=base, rodajas=rodajas, remate=remate, difusor=difusor())


def a_trimesh(m):
    s = m.to_mesh()
    return trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)


if __name__ == "__main__":
    p = construir()
    carpeta = AQUI / ("vista" if VISTA else "piezas")
    carpeta.mkdir(exist_ok=True)
    todas = [("base", p["base"]), ("remate", p["remate"]), ("difusor", p["difusor"])] + \
        [(f"rodaja_{i + 1:02d}", r) for i, r in enumerate(p["rodajas"])]
    for nombre, m in todas:
        t = a_trimesh(m)
        t.export(carpeta / f"{nombre}.stl")
        print(f"{nombre:10s} estanca={t.is_watertight} triángulos={len(t.faces)} tamaño={np.round(t.extents, 1)}")
