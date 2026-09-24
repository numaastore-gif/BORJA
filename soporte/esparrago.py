"""Espárragos roscados M5 para unir cada bola al soporte de la papelera.

Rosca exterior M5 x 0,8 a derechas en toda su longitud, a medida nominal (sin
holgura). Mide 23 mm: 11,5 entran en la caja y 11,5 en la bola; como los
agujeros tienen 12 mm, no hace tope y la bola asienta contra la caja. Punta
achaflanada en los dos extremos y ranura para destornillador arriba.
Se imprimen de pie (eje vertical), cuatro en una bandeja. Medidas en mm.

    python esparrago.py
"""
import pathlib

import numpy as np
import trimesh
from manifold3d import Manifold

from soporte import ROSCA, rosca_macho

LARGO = 23.0
CHAFLAN = 0.6
RANURA = dict(ancho=1.0, hondo=1.5)
SEPARACION = 12.0
CANTIDAD = 4


def esparrago():
    r = ROSCA["diametro"] / 2
    varilla = rosca_macho(LARGO)
    # chaflán en las dos puntas: doble cono que recorta las crestas
    c = CHAFLAN
    punta = Manifold.cylinder(LARGO, r, r, 64).translate((0, 0, 0))
    conos = Manifold.cylinder(c, r - c, r, 64) + \
        Manifold.cylinder(LARGO - 2 * c, r, r, 64).translate((0, 0, c)) + \
        Manifold.cylinder(c, r, r - c, 64).translate((0, 0, LARGO - c))
    ranura = Manifold.cube((2 * r + 1, RANURA["ancho"], RANURA["hondo"] + 1)) \
        .translate((-r - 0.5, -RANURA["ancho"] / 2, LARGO - RANURA["hondo"]))
    return (varilla ^ conos ^ punta) - ranura


def construir():
    e = esparrago()
    paso = ROSCA["diametro"] + SEPARACION
    return Manifold.compose([e.translate(((i % 2 - 0.5) * paso, (i // 2 - 0.5) * paso, 0))
                             for i in range(CANTIDAD)])


if __name__ == "__main__":
    m = construir().to_mesh()
    t = trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)
    t.export(pathlib.Path(__file__).with_name("esparragos.stl"))
    # uno suelto para la vista previa del visor (los cuatro juntos pesan demasiado)
    u = esparrago().to_mesh()
    trimesh.Trimesh(u.vert_properties[:, :3], u.tri_verts, process=False) \
        .export(pathlib.Path(__file__).with_name("esparrago_vista.stl"))
    print("estanca:", t.is_watertight, "| bandeja:", np.round(t.extents, 1), "| largo", LARGO, "mm")
