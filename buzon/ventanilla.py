"""Pieza de recambio para la ventanilla del buzón (la de plástico translúcido
que se partió).

Encaja por dentro del buzón en el hueco del reborde interior, de 70 × 20 mm:

  resalte   placa de 1 mm que entra en el hueco y queda a ras del reborde.
            Mide 0,1 mm menos por lado y lleva nervios de presión en los
            cantos que aprietan 0,15 mm: entra a presión y queda firme sin
            tener que forzar todo el contorno. Chaflán de entrada en el frente.
  pestaña   reborde de 3 mm alrededor, por detrás, que apoya contra el reborde
            interior del buzón e impide que la pieza se salga hacia fuera.

Se imprime plana, con la pestaña sobre la cama y sin soportes.
Medidas en mm.

    python ventanilla.py
"""
import pathlib

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, OpType

HUECO = (70.0, 20.0)       # reborde interior del buzón (largo × alto)
GROSOR = 1.0               # placa que entra en el hueco
HOLGURA = 0.1              # por lado; el apriete lo dan los nervios
RADIO_HUECO = 1.0          # esquinas del resalte
PESTANA = dict(ancho=3.0, grosor=0.8, radio=2.0)
CHAFLAN = 0.3              # entrada del resalte
NERVIO = dict(radio=0.8, aprieto=0.15, por_lado_largo=3, por_lado_corto=1)


def rectangulo(largo, alto, radio):
    return CrossSection.square((largo - 2 * radio, alto - 2 * radio), center=True).offset(radio, circular_segments=48)


def construir():
    l, a = HUECO[0] - 2 * HOLGURA, HUECO[1] - 2 * HOLGURA
    p = PESTANA
    pestana = rectangulo(HUECO[0] + 2 * p["ancho"], HUECO[1] + 2 * p["ancho"], p["radio"]).extrude(p["grosor"])
    # resalte con chaflán en el frente: tramo recto y tramo que se estrecha
    recto = rectangulo(l, a, RADIO_HUECO).extrude(GROSOR - CHAFLAN + 0.01).translate((0, 0, p["grosor"] - 0.01))
    punta = Manifold.batch_hull([
        rectangulo(l, a, RADIO_HUECO).extrude(0.01).translate((0, 0, p["grosor"] + GROSOR - CHAFLAN)),
        rectangulo(l - 2 * CHAFLAN, a - 2 * CHAFLAN, RADIO_HUECO - CHAFLAN / 2).extrude(0.01)
        .translate((0, 0, p["grosor"] + GROSOR - 0.01))])
    # nervios: medias cañas verticales en los cantos, que sobresalen
    # HOLGURA + aprieto del resalte y se pierden en el chaflán
    n = NERVIO
    sale = HOLGURA + n["aprieto"]
    alto_nervio = GROSOR - CHAFLAN
    cana = Manifold.cylinder(alto_nervio + 0.01, n["radio"], n["radio"], 32)
    nervios = []
    for x in np.linspace(-l / 2 + 12, l / 2 - 12, n["por_lado_largo"]):
        for s in (-1, 1):
            nervios.append(cana.translate((x, s * (a / 2 + sale - n["radio"]), p["grosor"] - 0.01)))
    for s in (-1, 1):
        nervios.append(cana.translate((s * (l / 2 + sale - n["radio"]), 0, p["grosor"] - 0.01)))
    pieza = Manifold.batch_boolean([pestana, recto, punta] + nervios, OpType.Add)
    m = pieza.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)


if __name__ == "__main__":
    malla = construir()
    malla.export(pathlib.Path(__file__).with_name("ventanilla_buzon.stl"))
    print("estanca:", malla.is_watertight, "| tamaño:", np.round(malla.extents, 2), "| volumen cm3:",
          round(malla.volume / 1000, 2))
