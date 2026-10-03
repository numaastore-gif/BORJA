"""Prepara la cabeza base a partir del escaneo «Infinite, 3D Head Scan» de Lee
Perry-Smith (CC BY 3.0, ver LeePerrySmith_License.txt; vía el repositorio de
three.js): la cierra (rehecha en vóxeles, con los ojos dentro), la corta en el
cuello con la base plana y la reduce a un número de triángulos manejable.
El resultado, cabeza_base.stl, tiene la frente hacia +x, la base del cuello en
z = 0 y está en las unidades del escaneo; cabezas.py la escala a cada talla.

    python base_cabeza.py
"""
import pathlib

import fast_simplification
import numpy as np
import trimesh
from scipy import ndimage
from skimage import measure

AQUI = pathlib.Path(__file__).parent
PASO = 0.02          # vóxel, en unidades del escaneo (~1 mm a la talla 57)
CUELLO = -1.5        # altura del corte del cuello (por debajo de la barbilla)
TRIANGULOS = 24000


def preparar():
    m = trimesh.load(AQUI / "LeePerrySmith.glb", force="mesh")
    # glTF va con y hacia arriba y la cara hacia +z: z arriba y cara hacia +x
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 0, 1]))
    lim = np.array([[m.bounds[0][0] - 3 * PASO, m.bounds[0][1] - 3 * PASO, CUELLO - 3 * PASO],
                    [m.bounds[1][0] + 3 * PASO, m.bounds[1][1] + 3 * PASO, m.bounds[1][2] + 3 * PASO]])
    forma = np.ceil((lim[1] - lim[0]) / PASO).astype(int) + 1
    ocupado = np.zeros(forma, bool)
    # superficie muestreada densamente (más fina que el vóxel)
    pts, _ = trimesh.sample.sample_surface_even(m, 3_000_000)
    pts = np.vstack([pts, m.vertices])
    idx = np.floor((pts - lim[0]) / PASO).astype(int)
    ok = np.all((idx >= 0) & (idx < forma), axis=1)
    ocupado[tuple(idx[ok].T)] = True
    ocupado = ndimage.binary_closing(ocupado, iterations=2)
    # rellena cada corte horizontal (cierra el interior de la cabeza)
    for k in range(forma[2]):
        ocupado[:, :, k] = ndimage.binary_fill_holes(ocupado[:, :, k])
    ocupado[:, :, :3] = ocupado[:, :, 3:4]   # el corte del cuello, recto
    vol = np.pad(ocupado, 2).astype(np.float32)
    vol = ndimage.gaussian_filter(vol, 0.8)
    v, f, _, _ = measure.marching_cubes(vol, 0.5)
    v = (v - 2) * PASO + lim[0]
    cab = trimesh.Trimesh(v, f[:, ::-1], process=True)
    cab = max(cab.split(only_watertight=False), key=lambda p: len(p.faces))
    vs, fs = fast_simplification.simplify(cab.vertices.astype(np.float32), cab.faces.astype(np.int64),
                                          target_reduction=1 - TRIANGULOS / len(cab.faces))
    cab = trimesh.Trimesh(vs, fs, process=True)
    trimesh.smoothing.filter_taubin(cab, iterations=10)
    # base plana: todo lo que quede por debajo del primer vóxel lleno se corta
    cab = cab.slice_plane([0, 0, CUELLO + PASO], [0, 0, 1], cap=True)
    cab.apply_translation([0, 0, -cab.bounds[0][2]])
    if cab.volume < 0:
        cab.invert()
    return cab


if __name__ == "__main__":
    cab = preparar()
    cab.export(AQUI / "cabeza_base.stl")
    print("estanca:", cab.is_watertight, "| triángulos:", len(cab.faces), "| tamaño:", cab.extents.round(2))
