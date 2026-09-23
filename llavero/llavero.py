"""Llavero de pala de pádel calcado de la foto (referencia.jpg).

Tres piezas para imprimir a la vez en PLA Matte de Bambu Lab, una por color:
  - azul   (Marine Blue): cabeza y cuello
  - negro  (Charcoal):    dibujos de la cara (X, franja, puente, logo) incrustados
  - blanco (Ivory White): mango completo y argolla
Los dibujos van incrustados 0,6 mm en las dos caras; el reverso lleva el
dibujo en espejo para que se lea bien al dar la vuelta al llavero. Los
agujeros de la cabeza y del cuello atraviesan la pieza. Medidas en mm.

    pip install numpy opencv-python-headless manifold3d trimesh
    python llavero.py
"""
import pathlib

import cv2
import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, JoinType, Manifold

AQUI = pathlib.Path(__file__).parent
FOTO = AQUI / "referencia.jpg"

LARGO = 70.0          # largo de la pala sin la argolla
GROSOR = 4.5
INCRUSTADO = 0.6      # profundidad de los dibujos negros en cada cara
TRAZO_MIN = 0.35      # se eliminan detalles más finos (no se pueden imprimir)
MOTA_MIN = 0.8        # mm²: manchas negras más pequeñas se descartan
ARGOLLA = dict(radio=3.8, agujero=1.7, separacion=3.0)

# Zonas de la foto (en píxeles)
Y_MANGO = 480         # donde empieza el mango (se hace entero blanco)
Y_FIN = 647           # final del mango; debajo está el colgante que se quita
SUBMUESTREO = 4       # contornos a 1/4 de píxel para que salgan suaves
HALO = 2.0            # px de brillo alrededor de los agujeros en la foto
LOGO = (295, 32, 405, 62)  # recuadro del logo «nox» de arriba (x0, y0, x1, y1)
LOGO_ALTO = 3.2       # mm; en la foto mide 2 mm, se agranda para que se imprima
BORDE = 0.5           # franja azul del marco que queda libre de dibujo

COLORES = {"azul": "#0078BF", "negro": "#000000", "blanco": "#FFFFFF"}  # PLA Matte


def mascaras():
    im = cv2.imread(str(FOTO))
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
    s, v = hsv[..., 1], hsv[..., 2]
    fondo = im.min(2) > 215
    # fondo conectado al borde = exterior; el resto del fondo son agujeros
    n, etiquetas = cv2.connectedComponents(fondo.astype(np.uint8))
    borde = set(np.unique(np.r_[etiquetas[0], etiquetas[-1], etiquetas[:, 0], etiquetas[:, -1]]))
    exterior = np.isin(etiquetas, list(borde)) & fondo
    filas = np.arange(im.shape[0])[:, None]
    pala = ~exterior & (filas < Y_FIN)
    agujeros = fondo & ~exterior & (filas < Y_MANGO)
    # negro y azul marino muy oscuro (franja, logo) y todo lo gris del carbono
    # de la X (cuadros claros y oscuros y su contorno) cuentan como negro
    oscuro = ((v < 100) | (s < 70)) & pala & ~agujeros & (filas < Y_MANGO)
    # rellena motas claras (letras diminutas) dentro de las zonas negras
    n, et, st, _ = cv2.connectedComponentsWithStats((~oscuro).astype(np.uint8))
    for i in range(n):
        if st[i, cv2.CC_STAT_AREA] < 250:
            oscuro[et == i] = True
    oscuro &= pala & ~agujeros & (filas < Y_MANGO)
    # quita motas oscuras sueltas (letras de menos de 1 mm una vez a escala)
    n, et, st, _ = cv2.connectedComponentsWithStats(oscuro.astype(np.uint8))
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 80:
            oscuro[et == i] = False
    return pala, agujeros, oscuro


def eje(pala):
    ys, xs = np.nonzero(pala[:Y_MANGO])
    return (xs.min() + xs.max()) / 2, ys.min()


def simetrica(m, x_eje):
    """Promedia una máscara con su reflejo respecto al eje de la pala."""
    f = m.astype(np.float32)
    ancho = f.shape[1]
    M = np.float32([[-1, 0, 2 * x_eje], [0, 1, 0]])
    espejo = cv2.warpAffine(f, M, (ancho, f.shape[0]))
    return (f + espejo) / 2


def a_seccion(m, x_eje, y_top, escala, suavizado=0.8):
    """Máscara (0-1) -> CrossSection en mm con contornos suaves."""
    f = cv2.GaussianBlur(np.asarray(m, np.float32), (0, 0), suavizado)
    f = cv2.resize(f, None, fx=SUBMUESTREO, fy=SUBMUESTREO, interpolation=cv2.INTER_CUBIC)
    b = (f > 0.5).astype(np.uint8)
    contornos, _ = cv2.findContours(b, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polis = []
    for c in contornos:
        c = cv2.approxPolyDP(c, 0.6, True)[:, 0, :].astype(float)
        if len(c) < 3:
            continue
        x = ((c[:, 0] + 0.5) / SUBMUESTREO - 0.5 - x_eje) * escala
        y = (y_top - ((c[:, 1] + 0.5) / SUBMUESTREO - 0.5)) * escala
        polis.append(np.c_[x, y])
    return CrossSection(polis, FillRule.EvenOdd)


def agujeros_redondos(agujeros, x_eje, y_top, escala):
    """Los agujeros pequeños se sustituyen por círculos iguales y simétricos;
    los grandes (cuello) se calcan."""
    n, et, st, cen = cv2.connectedComponentsWithStats(agujeros.astype(np.uint8))
    bolas, grandes = [], np.zeros_like(agujeros)
    for i in range(1, n):
        area = st[i, cv2.CC_STAT_AREA]
        if area < 20:
            continue
        if area < 400:
            bolas.append((cen[i][0] - x_eje, cen[i][1], np.sqrt(area / np.pi)))
        else:
            grandes |= et == i
    bolas = np.array(bolas)
    # radio medido + el halo claro que deja la foto alrededor de cada agujero
    r = np.median(bolas[:, 2]) + HALO
    # empareja cada agujero con su simétrico y promedia posiciones
    circulos = []
    for x, y, _ in bolas:
        d = np.hypot(bolas[:, 0] + x, bolas[:, 1] - y)
        j = np.argmin(d)
        xs, ys = (x - bolas[j, 0]) / 2, (y + bolas[j, 1]) / 2
        circulos.append(CrossSection.circle(r * escala, 48).translate((xs * escala, (y_top - ys) * escala)))
    return (CrossSection.compose(circulos),
            a_seccion(simetrica(grandes, x_eje), x_eje, y_top, escala), r * escala)


def rectangulo_redondeado(x0, y0, x1, y1, r):
    if r <= 0:
        return CrossSection.square((x1 - x0, y1 - y0)).translate((x0, y0))
    return CrossSection.batch_hull([CrossSection.circle(r, 32).translate((x, y))
                                    for x in (x0 + r, x1 - r) for y in (y0 + r, y1 - r)])


def logo_nox(alto):
    """Logo «nox» redibujado con las proporciones de la foto (letras de
    esquinas redondeadas, «o» rectangular y «x» de trazos cruzados)."""
    t, r, hueco = 0.28, 0.3, 0.3  # trazo, radio y separación (en alturas)
    n_ancho, o_ancho, x_ancho = 1.4, 1.45, 1.45
    n = rectangulo_redondeado(0, 0, n_ancho, 1, r) - \
        rectangulo_redondeado(t, -1, n_ancho - t, 1 - t, max(r - t, 0.02)) - \
        CrossSection.square((n_ancho, 1)).translate((0, -1))
    x0 = n_ancho + hueco
    o = rectangulo_redondeado(x0, 0, x0 + o_ancho, 1, r) - \
        rectangulo_redondeado(x0 + t, t, x0 + o_ancho - t, 1 - t, max(r - t, 0.02))
    x0 += o_ancho + hueco
    trazo = lambda a, b: CrossSection.batch_hull([CrossSection.circle(t / 2, 16).translate(p) for p in (a, b)])
    x = (trazo((x0 + t / 2, 1 - t / 2), (x0 + x_ancho - t / 2, t / 2)) +
         trazo((x0 + t / 2, t / 2), (x0 + x_ancho - t / 2, 1 - t / 2))) ^ \
        CrossSection.square((x_ancho, 1)).translate((x0, 0))
    total = n + o + x
    ancho = x0 + x_ancho
    return total.translate((-ancho / 2, -0.5)).scale((alto, alto))


def limpia(sec):
    """Quita trazos más finos que TRAZO_MIN (apertura morfológica)."""
    return sec.offset(-TRAZO_MIN / 2, JoinType.Round).offset(TRAZO_MIN / 2, JoinType.Round)


def construir():
    pala, agujeros, oscuro = mascaras()
    x_eje, y_top = eje(pala)
    escala = LARGO / (Y_FIN - y_top)

    silueta = a_seccion(simetrica(pala, x_eje), x_eje, y_top, escala)
    bolas, cuello, r_bola = agujeros_redondos(agujeros, x_eje, y_top, escala)
    huecos = bolas + cuello

    y_corte = -(Y_MANGO - y_top) * escala
    arriba = CrossSection.square((200, 200)).translate((-100, y_corte))
    abajo = CrossSection.square((200, 200)).translate((-100, y_corte - 200))
    cabeza = (silueta ^ arriba) - huecos
    mango = silueta ^ abajo

    # argolla bajo el mango
    y_fin = -LARGO
    a = ARGOLLA
    centro = (0.0, y_fin - a["separacion"])
    x0, _, x1, _ = mango.bounds()
    base = CrossSection.square((x1 - x0, 0.01)).translate((x0, y_fin))
    lengueta = CrossSection.batch_hull([CrossSection.circle(a["radio"], 64).translate(centro), base]) \
        - CrossSection.circle(a["agujero"], 48).translate(centro)
    mango = mango + lengueta

    x0, y0, x1, y1 = LOGO
    logo = np.zeros_like(oscuro)
    logo[y0:y1, x0:x1] = oscuro[y0:y1, x0:x1]
    oscuro[y0:y1, x0:x1] = 0
    ys, xs = np.nonzero(logo)
    cx = ((xs.min() + xs.max()) / 2 - x_eje) * escala
    cy = (y_top - (ys.min() + ys.max()) / 2) * escala
    logo = logo_nox(LOGO_ALTO).translate((cx, cy))
    # margen azul solo en el contorno exterior, no alrededor de los agujeros
    marco = (silueta ^ arriba).offset(-BORDE, JoinType.Round) - huecos
    dibujo = (limpia(a_seccion(oscuro, x_eje, y_top, escala, suavizado=0.5)) + logo) ^ marco
    dibujo = CrossSection.compose([p for p in dibujo.decompose() if p.area() >= MOTA_MIN])
    dibujo_reverso = dibujo.mirror((1, 0)) ^ cabeza

    negro = dibujo.extrude(INCRUSTADO).translate((0, 0, GROSOR - INCRUSTADO)) + \
        dibujo_reverso.extrude(INCRUSTADO)
    azul = cabeza.extrude(GROSOR) - negro
    blanco = mango.extrude(GROSOR)
    info = dict(escala=escala, agujero_bola=2 * r_bola)
    return dict(azul=azul, negro=negro, blanco=blanco), info


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
    print("tamaño mm:", np.round(todo.extents, 1), "| escala mm/px:", round(info["escala"], 4),
          "| agujeros de la cabeza Ø", round(info["agujero_bola"], 2), "mm")
