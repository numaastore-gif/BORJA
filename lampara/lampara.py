"""Lámpara «tronco» para numashome: un tronco realista, con presencia de pieza
de tienda de decoración (Ø ~150 × 330 mm), cortado en rodajas con rendijas de
luz. Pie con raíces en contrafuerte y pliegues entre ellas, ligera
inclinación, nudos con su abultamiento y la cicatriz de la rama, y en el corte
de arriba anillos de crecimiento, médula, grietas de secado y la línea de la
corteza:

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

# --- Forma del tronco -------------------------------------------------------------------------
# Radio medio según la altura (z, radio): pie que se abre en raíces y tronco
# que se estrecha muy poco hacia arriba.
PERFIL = [(0, 84.0), (8, 78.0), (22, 74.0), (45, 71.5), (100, 70.0), (180, 69.0),
          (260, 68.0), (360, 67.0)]
EJE = [(0, 0.0, 0.0), (360, 6.0, -3.0)]  # el tronco se inclina un poco
LOBULOS = [(2, 0.05), (3, 0.035), (4, 0.02), (5, 0.015), (7, 0.01)]  # (número, amplitud relativa)
RAICES = dict(cantidad=5, fuerza=11.0, ancho=(22.0, 32.0), alto=55.0)   # contrafuertes del pie
PLIEGUES = dict(cantidad=5, hondo=7.0, ancho=(8.0, 13.0), alto=80.0)    # surcos entre raíces
# Entrantes: surcos verticales en V afilada, de paredes desiguales, que recorren
# el tronco serpenteando (como en las piezas de referencia): (ángulo, hondo,
# ancho de la boca, asimetría, altura de inicio, altura de fin)
ENTRANTES = [(20.0, 11.0, 26.0, 1.5, 0, 400), (78.0, 8.0, 20.0, 0.7, 0, 230),
             (140.0, 12.0, 28.0, 1.3, 60, 400), (205.0, 9.0, 22.0, 0.6, 0, 400),
             (262.0, 7.0, 18.0, 1.7, 120, 400), (318.0, 10.0, 24.0, 0.8, 0, 300)]
# festoneado del borde: ondulaciones medianas como las del contorno de referencia
FESTONES = [(8, 0.018), (11, 0.016), (14, 0.012), (17, 0.01), (23, 0.007)]
SERPENTEO = dict(amplitud=9.0, periodo=140.0)  # cuánto se desvían los entrantes al subir
DESORDEN = dict(giro=1.5, desplazamiento=0.6)  # cada rodaja, apenas descolocada

# --- Alturas -----------------------------------------------------------------------------
ALTO_BASE = 100.0
RODAJAS = 14
GROSOR_RODAJA = 6.3     # como las rodajas de la referencia
RENDIJA = 3.0
ALTO_REMATE = 80.0
BISEL = 9.0

# --- Corte de arriba -------------------------------------------------------------------------
CORTE = dict(anillo_hondo=0.5, anillo_ancho=0.6, separacion=(2.5, 6.0), corteza=7.0,
             grietas=4, grieta_hondo=2.0, grieta_ancho=1.8, medula=2.0)

# --- Textura -------------------------------------------------------------------------
TEXTURA = AQUI / "textura_corteza.npy"
PIXEL = 0.3             # mm por píxel de la textura escaneada
GRIETAS_POR_CM2 = 0.07  # densidad de grietas
GRIETA = dict(largo=(14.0, 38.0), ancho=(1.2, 2.4), hondo=(1.2, 2.2), inclinacion=0.18)

# --- Difusor -------------------------------------------------------------------------
R_DIFUSOR = 30.0        # el difusor asienta justo encima del disco LED
ESCALON = 1.0
PARED_DIFUSOR = 1.6
GUIAS = (0.0, 150.0)
GUIA = dict(ancho=4.0, alto=2.0)
PESTANA = dict(radio=R_DIFUSOR + 3.0, grosor=3.0, lengueta=4.0)
HOLGURA = 0.2
ENTRA_EN_REMATE = 18.0

# --- Luz: Bambu Lab LED Lamp Kit 001 (disco de Ø 59 × 18 mm, cable de 1,5 m) --------------
# Alojamiento y recorrido del cable copiados de la base de referencia: disco en un
# hueco de Ø 62, estría vertical en la pared del hueco para la salida lateral del
# cable, ranura bajo el suelo hasta el agujero central de Ø 20 y salida por abajo.
LED = dict(diametro=62.0, alto=19.0)          # hueco del disco (Ø 59 + holgura)
AGUJERO_CENTRAL = 20.0
RANURA_CABLE = dict(ancho=4.0, hondo=6.0, largo=37.0, angulo=200.0)  # estría + ranura del suelo
SALIDA_CABLE = dict(ancho=4.0, alto=5.0)      # salida por la cara inferior hacia el lateral
TEXTO = "numa home"
TEXTO_ALTO = 8.0
TEXTO_HONDO = 0.6

Z_RODAJA = [ALTO_BASE + RENDIJA + i * (GROSOR_RODAJA + RENDIJA) for i in range(RODAJAS)]
Z_REMATE = Z_RODAJA[-1] + GROSOR_RODAJA + RENDIJA
ALTO_TOTAL = Z_REMATE + ALTO_REMATE
Z_TOPE = ALTO_TOTAL + np.tan(np.radians(BISEL)) * 95

rng = np.random.default_rng(SEMILLA)


# --- Contorno orgánico ---------------------------------------------------------------------
# las fases giran con la altura: el contorno cambia bastante de una pieza a otra
LOBULO_FASE = [(n, a, rng.uniform(0, 2 * np.pi), rng.uniform(-0.012, 0.012)) for n, a in LOBULOS]
SERPENTEO_FASE = [rng.uniform(0, 2 * np.pi) for _ in ENTRANTES]
FESTON_FASE = [(n, a, rng.uniform(0, 2 * np.pi), rng.uniform(-0.02, 0.02)) for n, a in FESTONES]
_paso = 2 * np.pi / RAICES["cantidad"]
RAIZ = [(k * _paso + rng.uniform(-0.25, 0.25), rng.uniform(*RAICES["ancho"]), rng.uniform(0.6, 1.0))
        for k in range(RAICES["cantidad"])]
PLIEGUE = [(a + _paso / 2 + rng.uniform(-0.15, 0.15), rng.uniform(*PLIEGUES["ancho"]), rng.uniform(0.6, 1.0))
           for a, _, _ in RAIZ]
R_MEDIO = 70.0
PERIMETRO = 2 * np.pi * R_MEDIO
ANGULOS = np.linspace(0, 2 * np.pi, int(PERIMETRO / RESOLUCION), endpoint=False)
ARCO = ANGULOS * R_MEDIO  # coordenada horizontal de la textura (mm)


def eje(z):
    zs, xs, ys = zip(*EJE)
    return np.interp(z, zs, xs), np.interp(z, zs, ys)


def radio(theta, z, detalle=True):
    """Radio del tronco en (ángulo, altura). Sin «detalle» no lleva los
    entrantes (se usa para dibujar los anillos del corte)."""
    r0 = np.interp(z, *zip(*PERFIL))
    r = np.full_like(theta, r0)
    for n, a, fase, giro in LOBULO_FASE:
        r *= 1 + a * np.cos(n * theta + fase + giro * z)
    # raíces en contrafuerte y surcos entre ellas, que se pierden hacia arriba
    for lista, conf, signo in ((RAIZ, RAICES, 1), (PLIEGUE, PLIEGUES, -1)):
        fuerza = np.clip(1 - z / conf["alto"], 0, 1) ** 2
        magnitud = conf.get("fuerza", conf.get("hondo"))
        for ang, ancho, k in lista:
            d = (theta - ang + np.pi) % (2 * np.pi) - np.pi
            r += signo * magnitud * k * fuerza * np.exp(-0.5 * (d * r0 / (ancho / 2)) ** 2)
    # entrantes en V afilada
    if detalle:
        for (ang, hondo, ancho, asim, z0, z1), fase in zip(ENTRANTES, SERPENTEO_FASE):
            if not (z0 - 20 <= z <= z1 + 20):
                continue
            entrada = np.clip((z - z0) / 20 + 1, 0, 1) if z0 > 0 else 1.0
            salida = np.clip((z1 - z) / 20 + 1, 0, 1)
            desvio = SERPENTEO["amplitud"] * np.sin(2 * np.pi * z / SERPENTEO["periodo"] + fase)
            da = ((theta - np.radians(ang) + np.pi) % (2 * np.pi) - np.pi) * r0 - desvio
            mitad = np.where(da < 0, ancho * asim / (1 + asim), ancho / (1 + asim))
            x = np.clip(np.abs(da) / mitad, 0, 1)
            r -= hondo * entrada * salida * 0.5 * (1 + np.cos(np.pi * x)) ** 1.2 / 2 ** 0.2
        for n, a, fase, giro in FESTON_FASE:
            r *= 1 + a * np.cos(n * theta + fase + giro * z)
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
def deformidades(theta, z):
    """Dentro de los entrantes la textura de corteza se suaviza (en el fondo de
    una V estrecha, el relieve completo haría que las paredes se cruzaran)."""
    hueco = radio(theta, z, detalle=False) - radio(theta, z)
    return 1 - 0.75 * np.clip(hueco / 6.0, 0, 1), np.zeros_like(theta)


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
        peso, extra = deformidades(ANGULOS - ge, z)
        d = veta(ARCO, z) * peso + grietas(ARCO, np.full_like(ARCO, z), lista) * peso + extra
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
    letras = letras.translate((-(x0 + x1) / 2, -(y0 + y1) / 2)).mirror((1, 0)).translate((0, -42.0))
    return letras.extrude(TEXTO_HONDO + 1).translate((0, 0, -1))


# --- Corte de arriba: anillos, médula, grietas y corteza ----------------------------------------
def dibujo_corte():
    """Surcos del corte superior en planta: (finos, hondos)."""
    r = np.random.default_rng(SEMILLA + 7)
    t = np.linspace(0, 2 * np.pi, 720, endpoint=False)
    cx, cy = eje(ALTO_TOTAL)
    borde = radio(t, ALTO_TOTAL, detalle=False)
    c = CORTE

    def banda(rr, ancho):
        fuera = np.c_[cx + rr * np.cos(t), cy + rr * np.sin(t)]
        dentro = np.c_[cx + (rr - ancho) * np.cos(t), cy + (rr - ancho) * np.sin(t)]
        return CrossSection([fuera]) - CrossSection([dentro])

    finos = [banda(borde - c["corteza"], 1.0)]  # línea entre corteza y madera
    k = c["corteza"] + r.uniform(*c["separacion"]) * 0.6
    while (borde - k).min() > 6:
        # los anillos se aprietan hacia fuera, como en la madera real
        onda = 0.5 * np.sin(r.integers(2, 6) * t + r.uniform(0, 6.3))
        finos.append(banda(borde - k + onda, c["anillo_ancho"]))
        k += r.uniform(*c["separacion"]) * (0.6 + 0.8 * k / borde.mean())
    hondos = [CrossSection.circle(c["medula"], 32).translate((cx, cy))]
    for _ in range(c["grietas"]):
        a = r.uniform(0, 2 * np.pi)
        r1, r2 = r.uniform(6, 14), borde.mean() * r.uniform(0.55, 0.9)
        curva = r.uniform(-0.08, 0.08)
        s = np.linspace(0, 1, 12)
        eje_r = r1 + (r2 - r1) * s
        eje_a = a + curva * s ** 2
        medio = c["grieta_ancho"] / 2 * np.sin(np.pi * s) ** 0.6 + 0.05
        izq = np.c_[eje_r * np.cos(eje_a) - medio * np.sin(eje_a), eje_r * np.sin(eje_a) + medio * np.cos(eje_a)]
        der = np.c_[eje_r * np.cos(eje_a) + medio * np.sin(eje_a), eje_r * np.sin(eje_a) - medio * np.cos(eje_a)]
        hondos.append(CrossSection([np.vstack([der, izq[::-1]]) + (cx, cy)], FillRule.EvenOdd))
    return (CrossSection.batch_boolean(finos, OpType.Add), CrossSection.batch_boolean(hondos, OpType.Add))


def grabar_corte(pieza):
    plano = corte_superior()
    coseno = np.cos(np.radians(BISEL))
    finos, hondos = dibujo_corte()
    for dibujo, hondo in ((finos, CORTE["anillo_hondo"]), (hondos, CORTE["grieta_hondo"])):
        prisma = dibujo.extrude(400).translate((0, 0, Z_REMATE))
        # la capa sobresale 1 mm por encima del corte: sin planos coincidentes
        capa = plano.translate((0, 0, 1.0)) - plano.translate((0, 0, -hondo / coseno))
        pieza = pieza - (prisma ^ capa)
    return pieza


# --- Piezas ------------------------------------------------------------------------------------------
def construir():
    base = bloque(0, ALTO_BASE, SEMILLA)
    asiento = Manifold.cylinder(PESTANA["grosor"] + 1, PESTANA["radio"] + HOLGURA, PESTANA["radio"] + HOLGURA, 180)
    for ang in GUIAS:
        asiento = asiento + Manifold.cube((PESTANA["lengueta"] + 1 + HOLGURA, 6.0 + 2 * HOLGURA, PESTANA["grosor"] + 1)) \
            .translate((PESTANA["radio"] - 1, -3.0 - HOLGURA, 0)).rotate((0, 0, ang))
    base = base - asiento.translate((0, 0, ALTO_BASE - PESTANA["grosor"]))
    z_led = ALTO_BASE - PESTANA["grosor"] - LED["alto"]  # suelo del hueco del disco
    base = base - Manifold.cylinder(LED["alto"] + 1, LED["diametro"] / 2, LED["diametro"] / 2, 180) \
        .translate((0, 0, z_led))
    base = base - Manifold.cylinder(z_led + 1, AGUJERO_CENTRAL / 2, AGUJERO_CENTRAL / 2, 96).translate((0, 0, -0.5))
    rc = RANURA_CABLE
    ranura = Manifold.cube((rc["largo"], rc["ancho"], rc["hondo"] + 0.5)) \
        .translate((0, -rc["ancho"] / 2, z_led - rc["hondo"]))
    estria = Manifold.cube((rc["largo"] - LED["diametro"] / 2 + 0.5, rc["ancho"], LED["alto"] + rc["hondo"])) \
        .translate((LED["diametro"] / 2 - 0.5, -rc["ancho"] / 2, z_led - rc["hondo"] + 0.01))
    base = base - (ranura + estria).rotate((0, 0, rc["angulo"]))
    canal = Manifold.cube((120, SALIDA_CABLE["ancho"], SALIDA_CABLE["alto"] + 0.5)) \
        .translate((0, -SALIDA_CABLE["ancho"] / 2, -0.5)).rotate((0, 0, rc["angulo"]))
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
    remate = grabar_corte(remate)
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
