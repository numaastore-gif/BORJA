"""Conjunto montado del soporte de la papelera, solo para verlo en el visor.

Las dos piezas del soporte encajadas, apoyadas sobre las cuatro bolas, con
los espárragos M5 metidos en sus roscas (11,5 mm en la caja y 11,5 en la
bola). Se exporta una malla por componente para darle a cada uno su color.
Los espárragos van con menos resolución: quedan ocultos dentro de las roscas.

    python conjunto.py
"""
import pathlib

import trimesh
from manifold3d import Manifold

import bola
import esparrago
import soporte

AQUI = pathlib.Path(__file__).parent


def construir():
    b, alto_bola = bola.bola()
    dx = soporte.EXTERIOR[0] / 2 - soporte.ROSCA_DESDE_BORDE
    dy = soporte.EXTERIOR[1] / 2 - soporte.ROSCA_DESDE_BORDE
    esquinas = [(sx * dx, sy * dy) for sx in (-1, 1) for sy in (-1, 1)]
    p1, p2 = soporte.piezas()
    subir = (0, 0, alto_bola)  # la caja apoya sobre la cara plana de arriba de las bolas
    e = esparrago.esparrago(puntos=24, por_vuelta=6)
    medio = esparrago.LARGO / 2
    return {
        "pieza_1": p1.translate(subir),
        "pieza_2": p2.translate(subir),
        "bolas": Manifold.compose([b.translate((x, y, 0)) for x, y in esquinas]),
        "esparragos": Manifold.compose([e.translate((x, y, alto_bola - medio)) for x, y in esquinas]),
    }


if __name__ == "__main__":
    for nombre, m in construir().items():
        s = m.to_mesh()
        t = trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)
        t.export(AQUI / f"conjunto_{nombre}.stl")
        print(f"{nombre:11s} estanca={t.is_watertight} triángulos={len(t.faces)}")
