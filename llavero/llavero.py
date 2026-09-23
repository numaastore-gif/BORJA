"""Llavero de pala de pádel a partir de la foto (referencia.jpg).

Tres piezas para imprimir a la vez en PLA Matte de Bambu Lab, una por color:
  - azul   (Marine Blue): cabeza y cuello
  - negro  (Charcoal):    dibujos incrustados en las dos caras y franja del mango
  - blanco (Ivory White): mango y argolla
Los dibujos se construyen con geometría limpia (rectas, arcos y contornos
suavizados y simétricos) a partir de medidas tomadas sobre la foto, para que
las líneas salgan rectas y nítidas al imprimir. Van incrustados 0,6 mm en las
dos caras; el reverso lleva el dibujo en espejo para que se lea igual al dar
la vuelta al llavero. Los agujeros atraviesan la pieza. Medidas en mm.

    pip install numpy opencv-python-headless manifold3d trimesh lxml
    python llavero.py
"""
import pathlib

import cv2
import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, JoinType

AQUI = pathlib.Path(__file__).parent
FOTO = AQUI / "referencia.jpg"

LARGO = 70.0          # largo de la pala sin la argolla
GROSOR = 4.5
INCRUSTADO = 0.6      # profundidad de los dibujos negros en cada cara
BORDE = 0.5           # franja azul del marco que queda libre de dibujo
MOTA_MIN = 0.8        # mm²: manchas negras más pequeñas se descartan
ARGOLLA = dict(radio=3.8, agujero=1.7, separacion=3.0)
LOGO_ALTO = 3.2       # mm; en la foto mide 2 mm, se agranda para que se imprima
SEPARACION = 5.0      # px: ancho de las líneas azules que dividen la X (0,55 mm)
SUAVIZADO = 2.5       # px: suavizado de los contornos calcados

COLORES = {"azul": "#0078BF", "negro": "#000000", "blanco": "#FFFFFF"}  # PLA Matte

# --- Medidas tomadas sobre la foto (píxeles) --------------------------------
EJE_X = 350.0         # eje de simetría de la pala
Y_TOP = 15.0          # punta superior de la cabeza
Y_MANGO = 480         # donde empieza el mango
Y_FRANJA = 498        # fin de la franja negra entre cabeza y mango
Y_FIN = 647           # final del mango (debajo estaba el colgante)
MANGO = [(480, 27.5), (500, 24.5), (636, 24.5), (647, 28.0)]  # (y, semiancho)
# X: puntas, vértice izquierdo, círculo de la muesca y líneas de separación
X_ARRIBA, X_ABAJO, X_IZQ, X_DER = 94.5, 283.5, 207.5, 492.0
X_VERTICE = 302.0
MUESCA = (406.5, 189.0, 32.0)
LINEA_1 = ((315.0, 124.5), (355.0, 150.0))  # separa la pieza izquierda
LINEA_2 = ((384.0, 124.0), (355.0, 149.0))  # separa el brazo derecho
ETIQUETA = (501.5, 166.0, 506.5, 212.0)     # etiqueta vertical del lateral
LOGO_CENTRO = (350.0, 47.0)
FRANJA_ZONA = (300, Y_MANGO)                # franja negra y puente del cuello

ESCALA = LARGO / (Y_FIN - Y_TOP)


def a_mm(puntos):
    p = np.asarray(puntos, float).reshape(-1, 2)
    return np.c_[(p[:, 0] - EJE_X) * ESCALA, (Y_TOP - p[:, 1]) * ESCALA]


def poligono(puntos):
    return CrossSection([a_mm(puntos)], FillRule.EvenOdd)


def circulo(cx, cy, r, n=96):
    return CrossSection.circle(r * ESCALA, n).translate(tuple(a_mm([(cx, cy)])[0]))


def redondeado(x0, y0, x1, y1, r):
    """Rectángulo con esquinas redondeadas (coordenadas ya en su unidad)."""
    r = min(r, (x1 - x0) / 2 - 1e-3, (y1 - y0) / 2 - 1e-3)
    return CrossSection.batch_hull([CrossSection.circle(r, 32).translate((x, y))
                                    for x in (x0 + r, x1 - r) for y in (y0 + r, y1 - r)])


# --- Contornos calcados, simétricos y suavizados ---------------------------
def simetrica(m):
    f = m.astype(np.float32)
    M = np.float32([[-1, 0, 2 * EJE_X], [0, 1, 0]])
    return (f + cv2.warpAffine(f, M, (f.shape[1], f.shape[0]))) / 2


def contorno_suave(campo, sub=4):
    """Campo 0-1 -> CrossSection con contornos suavizados (sin dientes)."""
    f = cv2.GaussianBlur(np.asarray(campo, np.float32), (0, 0), 1.0)
    f = cv2.resize(f, None, fx=sub, fy=sub, interpolation=cv2.INTER_CUBIC)
    cs, _ = cv2.findContours((f > 0.5).astype(np.uint8), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    sigma = SUAVIZADO * sub
    k = int(3 * sigma)
    w = np.exp(-0.5 * (np.arange(-k, k + 1) / sigma) ** 2)
    w /= w.sum()
    polis = []
    for c in cs:
        c = c[:, 0, :].astype(float)
        if len(c) < 2 * k + 3:
            continue
        ext = np.r_[c[-k:], c, c[:k]]  # suavizado circular a lo largo del contorno
        c = np.c_[np.convolve(ext[:, 0], w, "valid"), np.convolve(ext[:, 1], w, "valid")]
        c = cv2.approxPolyDP(c.astype(np.float32).reshape(-1, 1, 2), 0.3 * sub, True)[:, 0, :]
        if len(c) >= 3:
            polis.append(a_mm((c + 0.5) / sub - 0.5))
    return CrossSection(polis, FillRule.EvenOdd)


def mascaras():
    im = cv2.imread(str(FOTO))
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
    s, v = hsv[..., 1], hsv[..., 2]
    fondo = im.min(2) > 215
    n, et = cv2.connectedComponents(fondo.astype(np.uint8))
    borde = np.unique(np.r_[et[0], et[-1], et[:, 0], et[:, -1]])
    exterior = np.isin(et, borde) & fondo
    filas = np.arange(im.shape[0])[:, None]
    pala = ~exterior & (filas < Y_MANGO + 4)
    agujeros = fondo & ~exterior & (filas < Y_MANGO)
    oscuro = ((v < 100) | (s < 70)) & pala & ~agujeros
    return pala, agujeros, oscuro


# --- La X --------------------------------------------------------------------
def semiplano_bajo(p, q, abajo=True):
    """Semiplano por debajo (más y en la foto) o por encima de la recta p-q."""
    (x1, y1), (x2, y2) = p, q
    m = (y2 - y1) / (x2 - x1)
    y_a, y_b = y1 + m * (-1000 - x1), y1 + m * (2000 - x1)
    lejos = 3000 if abajo else -3000
    return poligono([(-1000, y_a), (2000, y_b), (2000, lejos), (-1000, lejos)])


def banda(p, q, ancho, largo=500):
    p, q = np.array(p, float), np.array(q, float)
    d = (q - p) / np.linalg.norm(q - p)
    n = np.array([-d[1], d[0]]) * ancho / 2
    a, b = p - d * largo, p + d * largo
    return poligono([a + n, b + n, b - n, a - n])


def la_x():
    """Silueta de rectas a 45°, muesca circular a la derecha y líneas de
    separación entre sus cinco piezas; simétrica respecto a su horizontal."""
    yc = (X_ARRIBA + X_ABAJO) / 2
    v_der = X_DER - (yc - X_ARRIBA)
    x = poligono([(X_IZQ, X_ARRIBA), (X_DER, X_ARRIBA), (v_der, yc),
                  (X_DER, X_ABAJO), (X_IZQ, X_ABAJO), (X_VERTICE, yc)]) - circulo(*MUESCA)
    espejo = lambda l: tuple((px, 2 * yc - py) for px, py in l)
    mitad_sup = semiplano_bajo((0, yc), (1, yc), abajo=False)
    mitad_inf = semiplano_bajo((0, yc), (1, yc), abajo=True)
    for l1, l2, mitad, fuera_l1 in ((LINEA_1, LINEA_2, mitad_sup, False),
                                    (espejo(LINEA_1), espejo(LINEA_2), mitad_inf, True)):
        # la línea 1 llega hasta la muesca; la 2 termina al cruzarse con la 1
        x = x - (banda(*l1, SEPARACION) ^ mitad)
        x = x - (banda(*l2, SEPARACION) ^ mitad ^ semiplano_bajo(*l1, abajo=fuera_l1))
    return x


# --- Logo ----------------------------------------------------------------------
def logo_nox(alto):
    """Logo «nox» medido sobre el recorte del logo de la pala (unidades: la
    altura de las letras). «n» y «o» casi cuadradas con esquinas poco
    redondeadas; «x» formada por un chevron «>» con muesca en V a la
    izquierda y dos cuñas en diagonal a la derecha."""
    poli = lambda pts: CrossSection([np.array(pts, float)], FillRule.EvenOdd)
    n_w, o_w = 1.52, 1.54
    g1, g2 = 0.21, 0.18
    # «n»: solo las esquinas de arriba redondeadas; las patas acaban rectas
    n = (redondeado(0, -0.5, n_w, 1, 0.12) ^ CrossSection.square((n_w, 1))) - \
        redondeado(0.30, -1, n_w - 0.30, 1 - 0.25, 0.05)
    x0 = n_w + g1
    o = redondeado(x0, 0, x0 + o_w, 1, 0.18) - redondeado(x0 + 0.31, 0.24, x0 + o_w - 0.31, 1 - 0.25, 0.05)
    x0 += o_w + g2
    chevron = poli([(x0 + 0.03, 1), (x0 + 0.46, 1), (x0 + 0.93, 0.5), (x0 + 0.45, 0),
                    (x0 + 0.01, 0), (x0 + 0.46, 0.5)])
    cuna_arriba = poli([(x0 + 0.98, 0.68), (x0 + 1.22, 1), (x0 + 1.50, 1), (x0 + 1.10, 0.57)])
    cuna_abajo = poli([(x0 + 0.98, 0.32), (x0 + 1.10, 0.43), (x0 + 1.50, 0), (x0 + 1.22, 0)])
    total = n + o + chevron + cuna_arriba + cuna_abajo
    return total.translate((-(x0 + 1.50) / 2, -0.5)).scale((alto, alto))


# --- Agujeros -----------------------------------------------------------------
def agujeros_limpios(agujeros):
    """Agujeros de bola: círculos iguales, en filas y simétricos. Aberturas del
    cuello: contorno calcado, simétrico y suavizado."""
    n, et, st, cen = cv2.connectedComponentsWithStats(agujeros.astype(np.uint8))
    bolas, grandes = [], np.zeros_like(agujeros)
    for i in range(1, n):
        area = st[i, cv2.CC_STAT_AREA]
        if area < 20:
            continue
        if area < 400:
            bolas.append((cen[i][0] - EJE_X, cen[i][1], np.sqrt(area / np.pi)))
        else:
            grandes |= et == i
    bolas = np.array(bolas)
    r = np.median(bolas[:, 2]) + 2.0  # + el halo claro de la foto
    circulos = []
    for x, y, _ in bolas:
        j = np.argmin(np.hypot(bolas[:, 0] + x, bolas[:, 1] - y))
        xs = (x - bolas[j, 0]) / 2
        fila = bolas[np.abs(bolas[:, 1] - y) < 5, 1].mean()
        circulos.append(circulo(EJE_X + xs, fila, r, 48))
    return CrossSection.compose(circulos), contorno_suave(simetrica(grandes)), r * ESCALA


# --- Montaje --------------------------------------------------------------------
def construir():
    pala, agujeros, oscuro = mascaras()
    silueta = contorno_suave(simetrica(pala))
    bolas, cuello, r_bola = agujeros_limpios(agujeros)
    huecos = bolas + cuello

    corte = a_mm([(0, Y_MANGO)])[0][1]
    arriba = CrossSection.square((200, 200)).translate((-100, corte))
    cabeza = (silueta ^ arriba) - huecos

    # mango geométrico con la franja negra arriba y la argolla abajo
    lado = [(EJE_X + w, y) for y, w in MANGO]
    mango = poligono(lado + [(2 * EJE_X - x, y) for x, y in reversed(lado)])
    y_franja = a_mm([(0, Y_FRANJA)])[0][1]
    franja = mango ^ CrossSection.square((200, 200)).translate((-100, y_franja))
    mango = mango - franja
    y_fin = a_mm([(0, Y_FIN)])[0][1]
    a = ARGOLLA
    centro = (0.0, y_fin - a["separacion"])
    x0, _, x1, _ = mango.bounds()
    base = CrossSection.square((x1 - x0 - 1.0, 2.0)).translate((x0 + 0.5, y_fin))
    lengueta = CrossSection.batch_hull([CrossSection.circle(a["radio"], 64).translate(centro), base]) \
        - CrossSection.circle(a["agujero"], 48).translate(centro)
    mango = mango + lengueta

    # franja negra de abajo de la cabeza y puente del cuello (calcados)
    y0, y1 = FRANJA_ZONA
    zona = np.zeros_like(oscuro)
    zona[y0:y1] = oscuro[y0:y1]
    n, et, st, _ = cv2.connectedComponentsWithStats(zona.astype(np.uint8))
    zona = et == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    n, et, st, _ = cv2.connectedComponentsWithStats((~zona).astype(np.uint8))
    for i in range(n):  # rellena las letras diminutas de dentro
        if st[i, cv2.CC_STAT_AREA] < 400:
            zona[et == i] = True
    franja_cuello = contorno_suave(simetrica(zona))

    (ex0, ey1), (ex1, ey0) = a_mm([ETIQUETA[:2], ETIQUETA[2:]])
    etiqueta = redondeado(ex0, ey0, ex1, ey1, 0.3)
    logo = logo_nox(LOGO_ALTO).translate(tuple(a_mm([LOGO_CENTRO])[0]))
    marco = (silueta ^ arriba).offset(-BORDE, JoinType.Round) - huecos
    dibujo = (la_x() + franja_cuello + etiqueta) ^ marco
    dibujo = CrossSection.compose([p for p in dibujo.decompose() if p.area() >= MOTA_MIN])
    dibujo = dibujo + (logo ^ marco)  # el logo va entero, con sus cuñas pequeñas
    dibujo_reverso = dibujo.mirror((1, 0)) ^ marco

    # Cada cara sin cuellos de anchura cero (al guardar en STL darían aristas
    # compartidas por más de dos caras); el azul es el resto de la cabeza.
    abre = lambda c: c.offset(-0.03, JoinType.Round).offset(0.03, JoinType.Round).simplify(0.01)
    cabeza, mango, franja = cabeza.simplify(0.01), abre(mango), abre(franja)

    def reparto(d):
        # 0,08 mm de separación con los agujeros para que lo negro no los roce
        return abre(cabeza - abre(cabeza - abre(d)) - huecos.offset(0.08, JoinType.Round))

    capa = lambda c, z0, z1: c.extrude(z1 - z0).translate((0, 0, z0))
    negro = capa(reparto(dibujo), GROSOR - INCRUSTADO, GROSOR) + \
        capa(reparto(dibujo_reverso), 0, INCRUSTADO) + franja.extrude(GROSOR)
    azul = cabeza.extrude(GROSOR) - negro
    blanco = mango.extrude(GROSOR)
    return dict(azul=azul, negro=negro, blanco=blanco), dict(agujero_bola=2 * r_bola)


def a_trimesh(m):
    malla = m.to_mesh()
    return trimesh.Trimesh(malla.vert_properties[:, :3], malla.tri_verts, process=False)


if __name__ == "__main__":
    piezas, info = construir()
    escena = trimesh.Scene()
    for nombre, solido in piezas.items():
        t = a_trimesh(solido)
        t.visual.face_colors = trimesh.visual.color.hex_to_rgba(COLORES[nombre])
        t.export(AQUI / f"llavero_{nombre}.stl")
        escena.add_geometry(t, node_name=nombre, geom_name=nombre)
        print(f"{nombre:6s} estanca={t.is_watertight} volumen={t.volume / 1000:.2f} cm3")
    escena.export(AQUI / "llavero.3mf")
    todo = trimesh.util.concatenate(list(escena.geometry.values()))
    print("tamaño mm:", np.round(todo.extents, 1), "| agujeros de la cabeza Ø",
          round(info["agujero_bola"], 2), "mm")
