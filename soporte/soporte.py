"""Soporte para papelera, según el croquis (croquis.png), sin ruedas.

Bandeja rectangular: exterior 380 x 300 mm, hueco interior 340 x 260 mm donde
encaja la papelera (marco de 20 mm por lado), fondo macizo y borde alrededor.
Primer modelo: las alturas no vienen en el croquis y son una propuesta.

    pip install numpy trimesh manifold3d
    python soporte.py
"""
import pathlib

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

EXTERIOR = (380.0, 300.0)
INTERIOR = (340.0, 260.0)
FONDO = 4.0           # grosor del fondo
BORDE = 25.0          # altura del borde por encima del fondo
RADIO_EXT = 15.0      # esquinas redondeadas por fuera
RADIO_INT = 8.0       # y por dentro (la papelera suele tener esquinas curvas)
CHAFLAN = 2.0         # chaflán en los cantos de arriba y de abajo


def rectangulo(ancho, largo, r):
    return CrossSection.batch_hull([CrossSection.circle(r, 64).translate((x, y))
                                    for x in (-ancho / 2 + r, ancho / 2 - r)
                                    for y in (-largo / 2 + r, largo / 2 - r)])


def bloque(ancho, largo, r, alto, chaflan):
    """Prisma de esquinas redondeadas con los cantos de arriba y abajo achaflanados."""
    c = chaflan
    capas = [rectangulo(ancho - 2 * c, largo - 2 * c, r - c).extrude(0.01),
             rectangulo(ancho, largo, r).extrude(0.01).translate((0, 0, c)),
             rectangulo(ancho, largo, r).extrude(0.01).translate((0, 0, alto - c - 0.01)),
             rectangulo(ancho - 2 * c, largo - 2 * c, r - c).extrude(0.01).translate((0, 0, alto - 0.01))]
    return Manifold.batch_hull(capas)


def construir():
    alto = FONDO + BORDE
    cuerpo = bloque(*EXTERIOR, RADIO_EXT, alto, CHAFLAN)
    hueco = rectangulo(*INTERIOR, RADIO_INT).extrude(BORDE + 1).translate((0, 0, FONDO))
    return cuerpo - hueco


if __name__ == "__main__":
    s = construir().to_mesh()
    t = trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)
    t.export(pathlib.Path(__file__).with_name("soporte.stl"))
    print("estanca:", t.is_watertight, "| tamaño mm:", np.round(t.extents, 1),
          "| volumen cm3:", round(t.volume / 1000))
