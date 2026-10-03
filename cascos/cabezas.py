"""Cabezas de medida para cascos: de 50 a 65 cm de contorno, de centímetro en
centímetro (16 cabezas), todas en un único STL; en el laminador se separan con
«Dividir en objetos» y se reparten en las camas.

Cada cabeza es la parte de arriba de una cabeza (lo que entra en el casco):

  banda    20 mm verticales abajo cuyo contorno exterior es justo la talla
           (perímetro a la altura de la frente, donde se mide la talla del
           casco), con planta de huevo: 0,8 de ancho respecto al largo y la
           nuca algo más ancha que la frente.
  bóveda   se cierra hacia la coronilla con perfil de superelipse (más plana
           arriba, como una cabeza) y la coronilla algo hacia atrás.
  medida   la talla grabada en la frente («57 cm») y en grande en la
           coronilla, 0,8 mm de hondo para no cambiar el contorno.

Son macizas: se imprimen de pie sobre la banda, con relleno
bajo (mejor «relámpago», que solo sostiene la superficie de arriba).
Medidas en mm.

    python cabezas.py            # cabezas_50_65.stl, para imprimir
    python cabezas.py --vista    # cabezas_vista.stl, ligera para el visor
"""
import pathlib
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, Manifold, Mesh, OpType, triangulate
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath

TALLAS = range(50, 66)          # contorno en cm
ANCHO_LARGO = 0.80              # anchura / longitud de la planta
HUEVO = 0.07                    # la frente, algo más estrecha que la nuca
BANDA = 20.0
ALTO_BOVEDA = 0.155             # alto de la bóveda respecto al contorno
PLANA = 2.4                     # exponente de la superelipse de la bóveda
CORONILLA_ATRAS = 0.08          # la coronilla, desplazada hacia la nuca (fracción del largo)
VISTA = "--vista" in sys.argv   # versión ligera para el visor
PUNTOS = 140 if VISTA else 300
FILAS = 16 if VISTA else 32
TEXTO = dict(frente=11.0, coronilla=0.16, hondo=0.8)  # alto de letra en la frente (mm) y arriba (× largo)
SEPARACION = 15.0


def planta(contorno):
    """Contorno en planta (antihorario, frente hacia +x) con el perímetro pedido."""
    t = np.linspace(0, 2 * np.pi, PUNTOS, endpoint=False)
    p = np.c_[np.cos(t), ANCHO_LARGO * np.sin(t) * (1 - HUEVO * np.cos(t))]
    largo = np.linalg.norm(np.roll(p, -1, 0) - p, axis=1).sum()
    return p * contorno / largo


def solido(contorno):
    base = planta(contorno)
    a = base[:, 0].max()
    centro = np.array([-CORONILLA_ATRAS * a, 0.0])
    alto = ALTO_BOVEDA * contorno
    anillos, zs = [base, base], [0.0, BANDA]
    for k in range(1, FILAS):
        u = k / FILAS
        z = BANDA + alto * u
        s = (1 - u ** PLANA) ** (1 / PLANA)
        anillos.append(centro + (base - centro) * s)
        zs.append(z)
    n = PUNTOS
    pts = np.vstack([np.c_[r, np.full(n, z)] for r, z in zip(anillos, zs)])
    caras = []
    for f in range(len(anillos) - 1):
        i = f * n + np.arange(n)
        j = f * n + (np.arange(n) + 1) % n
        caras += [np.c_[i, j, j + n], np.c_[i, j + n, i + n]]
    cima = len(pts)
    pts = np.vstack([pts, [*centro, BANDA + alto]])
    ultimo = (len(anillos) - 1) * n
    i = np.arange(n)
    caras.append(np.c_[ultimo + i, ultimo + (i + 1) % n, np.full(n, cima)])
    caras.append(triangulate([base])[:, ::-1])
    m = Manifold(Mesh(vert_properties=pts.astype(np.float32), tri_verts=np.vstack(caras).astype(np.uint32)))
    return m, base, alto


def letras(texto, alto):
    prop = FontProperties(family="DejaVu Sans", weight="bold")
    escala = alto / TextPath((0, 0), "0", size=1.0, prop=prop).get_extents().height
    ruta = TextPath((0, 0), texto, size=1.0, prop=prop)
    c = CrossSection([p * escala for p in ruta.to_polygons() if len(p) > 2], FillRule.EvenOdd)
    x0, y0, x1, y1 = c.bounds()
    return c.translate((-(x0 + x1) / 2, -(y0 + y1) / 2))


def cabeza(talla):
    m, base, alto = solido(talla * 10.0)
    h = TEXTO["hondo"]
    # frente: el texto, proyectado desde delante, se queda en la piel de h mm
    # de la banda (solo por delante de x = 0, para no marcar la nuca)
    dentro = CrossSection([base]).offset(-h).extrude(BANDA + 2).translate((0, 0, -1))
    frente = letras(f"{talla} cm", TEXTO["frente"]).extrude(200).rotate((90, 0, 90)) \
        .translate((0, 0, BANDA / 2)) - dentro
    # coronilla: se lee mirando la cabeza desde delante y arriba; se quita lo
    # que queda a menos de h mm por debajo de la superficie
    a = base[:, 0].max()
    arriba = letras(str(talla), TEXTO["coronilla"] * 2 * a).rotate(90).extrude(400) \
        .translate((-CORONILLA_ATRAS * a, 0, BANDA)) - m.translate((0, 0, -h))
    return m - frente - arriba


if __name__ == "__main__":
    tallas = list(TALLAS)
    paso_x = np.ptp(planta(tallas[-1] * 10.0)[:, 0]) + SEPARACION
    paso_y = np.ptp(planta(tallas[-1] * 10.0)[:, 1]) + SEPARACION
    columnas = 4
    todas = []
    for k, t in enumerate(tallas):
        fila, col = divmod(k, columnas)
        c = cabeza(t)
        todas.append(c.translate((col * paso_x, -fila * paso_y, 0)))
        s = c.to_mesh()
        b = trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)
        print(f"{t} cm: {np.round(b.extents, 1)} mm, perímetro de la banda "
              f"{np.linalg.norm(np.diff(np.vstack([planta(t * 10.0), planta(t * 10.0)[:1]]), axis=0), axis=1).sum() / 10:.2f} cm")
    s = Manifold.batch_boolean(todas, OpType.Add).to_mesh()
    malla = trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)
    malla.export(pathlib.Path(__file__).with_name("cabezas_vista.stl" if VISTA else "cabezas_50_65.stl"))
    print("estanca:", malla.is_watertight, "| cuerpos:", malla.body_count, "| conjunto:", np.round(malla.extents, 0))
