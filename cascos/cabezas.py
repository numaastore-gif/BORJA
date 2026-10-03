"""Cabezas de medida para cascos: de 50 a 65 cm de contorno, de centímetro en
centímetro (16 cabezas), todas en un único STL; en el laminador se separan con
«Dividir en objetos» y se reparten en las camas.

Cada cabeza es la cabeza base (cabeza_base.stl, del escaneo de Lee Perry-Smith,
CC BY 3.0) escalada para que su contorno, medido donde se mide la talla de un
casco (el perímetro máximo por encima de las cejas, como la cinta de la imagen
de referencia), sea exactamente la talla. En la nuca lleva grabado:

    Cabeza nº 8
    Eje largo - 20,3 cm     (de la frente a la nuca, en la línea del contorno)
    Eje corto - 15,2 cm     (de lado a lado, en la misma línea)
    Contorno - 57 cm
    Talla - 57

Macizas, de pie sobre la base plana del cuello, sin soportes; con relleno bajo
(mejor «relámpago»). Medidas en mm.

    python base_cabeza.py   # una vez: prepara cabeza_base.stl
    python cabezas.py            # cabezas_50_65.stl y una por talla en cabezas/
    python cabezas.py --vista    # cabezas_vista.stl, ligera para el visor
"""
import pathlib
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, Manifold, Mesh, OpType
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

AQUI = pathlib.Path(__file__).parent
VISTA = "--vista" in sys.argv
TALLAS = range(50, 66)                 # contorno en cm
LINEA = (3.4, 4.4)                     # alturas (en la cabeza base) donde se busca el contorno máximo
TEXTO = dict(alto=0.0115, interlinea=1.55, hondo=1.0, bajo_linea=0.06)  # alto × contorno; bloque bajo la línea (× contorno)
SEPARACION = 15.0


def contorno_en(m, z):
    s = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    if s is None:
        return 0.0, None
    lazo = max(s.discrete, key=lambda d: np.linalg.norm(np.diff(d, axis=0), axis=1).sum())
    return np.linalg.norm(np.diff(lazo, axis=0), axis=1).sum(), lazo


def medir(m):
    """Altura, perímetro y lazo del contorno máximo por encima de las cejas."""
    mejor = max(((z, *contorno_en(m, z)) for z in np.linspace(*LINEA, 41)), key=lambda t: t[1])
    return mejor


def texto_cm(v):
    return f"{v:.1f}".replace(".", ",")


def bloque_texto(lineas, alto):
    prop = FontProperties(family="DejaVu Sans", weight="bold")
    escala = alto / TextPath((0, 0), "0", size=1.0, prop=prop).get_extents().height
    polis = []
    for k, linea in enumerate(lineas):
        ruta = TextPath((0, 0), linea, size=1.0, prop=prop)
        y = -k * alto * TEXTO["interlinea"]
        polis += [p * escala + (0, y) for p in ruta.to_polygons() if len(p) > 2]
    c = CrossSection(polis, FillRule.EvenOdd)
    x0, y0, x1, y1 = c.bounds()
    return c.translate((-(x0 + x1) / 2, -(y0 + y1) / 2))


def cabeza(base, numero, talla):
    contorno = talla * 10.0
    z0, per, lazo = medir(base)
    k = contorno / per
    m = base.copy()
    m.apply_scale(k)
    largo, corto = np.ptp(lazo[:, 0]) * k / 10, np.ptp(lazo[:, 1]) * k / 10
    zl = z0 * k
    # centro de la cabeza en planta, en la línea del contorno
    cx, cy = (lazo[:, :2].min(0) + lazo[:, :2].max(0)) / 2 * k
    lineas = [f"Cabeza nº {numero}", f"Eje largo - {texto_cm(largo)} cm", f"Eje corto - {texto_cm(corto)} cm",
              f"Contorno - {talla} cm", f"Talla - {talla}"]
    letras = bloque_texto(lineas, TEXTO["alto"] * contorno)
    # prisma hacia la nuca (-x): u -> -y (se lee desde detrás), v -> z
    prisma = letras.extrude(400).transform([[0, 0, -1, cx], [-1, 0, 0, cy], [0, 1, 0, zl - TEXTO["bajo_linea"] * contorno]])
    s = Manifold(Mesh(vert_properties=m.vertices.astype(np.float32), tri_verts=m.faces.astype(np.uint32)))
    # se graba lo que queda a menos de «hondo» mm de la superficie de la nuca
    grabado = prisma - s.translate((TEXTO["hondo"], 0, 0))
    return s - grabado, largo, corto


if __name__ == "__main__":
    base = trimesh.load(AQUI / "cabeza_base.stl")
    if VISTA:
        import fast_simplification
        v, f = fast_simplification.simplify(base.vertices.astype(np.float32), base.faces.astype(np.int64),
                                            target_reduction=0.85)
        base = trimesh.Trimesh(v, f, process=True)
    tallas = list(TALLAS)
    piezas = [cabeza(base, i, t) for i, t in enumerate(tallas, 1)]
    x0, y0, _, x1, y1, _ = piezas[-1][0].bounding_box()
    paso_x, paso_y = x1 - x0 + SEPARACION, y1 - y0 + SEPARACION
    todas = []
    for n, (t, (p, largo, corto)) in enumerate(zip(tallas, piezas)):
        fila, col = divmod(n, 4)
        todas.append(p.translate((col * paso_x, -fila * paso_y, 0)))
        if not VISTA:  # y cada cabeza en su propio STL, centrada y apoyada en z = 0
            carpeta = AQUI / "cabezas"
            carpeta.mkdir(exist_ok=True)
            u = p.to_mesh()
            una = trimesh.Trimesh(u.vert_properties[:, :3], u.tri_verts, process=False)
            c = una.bounds.mean(0)
            una.apply_translation([-c[0], -c[1], -una.bounds[0][2]])
            una.export(carpeta / f"cabeza_{n + 1:02d}_{t}cm.stl")
        b = p.to_mesh().vert_properties[:, :3]
        print(f"nº {n + 1:2d}  contorno {t} cm  eje largo {texto_cm(largo)}  eje corto {texto_cm(corto)}  "
              f"tamaño {np.round(np.ptp(b, axis=0), 1)} mm")
    s = Manifold.batch_boolean(todas, OpType.Add).to_mesh()
    malla = trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)
    malla.export(AQUI / ("cabezas_vista.stl" if VISTA else "cabezas_50_65.stl"))
    print("estanca:", malla.is_watertight, "| cuerpos:", malla.body_count, "| triángulos:", len(malla.faces))
