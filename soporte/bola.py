"""Bolas de apoyo del soporte de la papelera (cuatro, en una bandeja de impresión).

Esfera cortada en plano por abajo (apoya en el suelo y en la cama de la
impresora) y por arriba (asienta contra la caja). Arriba lleva una rosca
hembra M5 de 12 mm con el surco del filete más hondo: un espárrago M5 une bola y caja, y se
desenrosca para limpiar las bolas. Medidas en mm.

    python bola.py
"""
import pathlib

import numpy as np
import trimesh
from manifold3d import Manifold

from soporte import ROSCA, rosca_hembra

DIAMETRO = 45.0
CORTE_ABAJO = 2.0     # lo que se quita por abajo (apoyo plano de ~18 mm)
CORTE_ARRIBA = 3.0    # lo que se quita por arriba (asiento plano de ~22 mm)
PROFUNDIDAD_ROSCA = 12.0
SURCO_EXTRA = 0.25    # mm más de hondo en el surco del filete (radial), para los
                      # tornillos que se fabricarán; el agujero sigue a medida M5
SEPARACION = 12.0     # hueco entre bolas en la bandeja
CANTIDAD = 4


def bola():
    r = DIAMETRO / 2
    alto = DIAMETRO - CORTE_ABAJO - CORTE_ARRIBA
    esfera = Manifold.sphere(r, 128).translate((0, 0, r - CORTE_ABAJO))
    caja = Manifold.cube((DIAMETRO + 2, DIAMETRO + 2, alto)).translate((-r - 1, -r - 1, 0))
    # girada 180° (no reflejada: un espejo la volvería a izquierdas); entra por arriba
    rosca = rosca_hembra(PROFUNDIDAD_ROSCA, SURCO_EXTRA).rotate((180, 0, 0)).translate((0, 0, alto))
    return (esfera ^ caja) - rosca, alto


def construir():
    b, alto = bola()
    paso = DIAMETRO + SEPARACION
    return Manifold.compose([b.translate(((i % 2 - 0.5) * paso, (i // 2 - 0.5) * paso, 0))
                             for i in range(CANTIDAD)]), alto


if __name__ == "__main__":
    bolas, alto = construir()
    m = bolas.to_mesh()
    t = trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)
    t.export(pathlib.Path(__file__).with_name("bolas.stl"))
    print("estanca:", t.is_watertight, "| alto de cada bola:", alto, "mm | rosca M5 de",
          PROFUNDIDAD_ROSCA, "mm | bandeja:", np.round(t.extents, 1))
