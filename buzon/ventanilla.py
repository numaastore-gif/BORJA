"""Pieza de recambio para la ventanilla del buzón (la de plástico translúcido
que se partió).

Encaja por dentro del buzón en el hueco del reborde interior, de 70 × 20 mm:

  resalte   placa de 1 mm que entra en el hueco y queda a ras del reborde.
            Mide 0,1 mm menos por lado y lleva nervios finos en los cantos
            que aprietan solo 0,08 mm y van en rampa (de cero en el frente al
            máximo junto a la pestaña): el apriete lo absorben los propios
            nervios al aplastarse, no la placa, así que la pieza no se tensa
            ni se parte al encajarla. Chaflán de entrada en el frente.
  pestaña   reborde de 3 mm alrededor, por detrás, de 1,2 mm de grosor para
            que sea robusta, que apoya contra el reborde interior del buzón e
            impide que la pieza se salga hacia fuera.

Se encaja empujando recto, sin doblarla. Mejor en PETG (más tenaz que el PLA).

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
PESTANA = dict(ancho=3.0, grosor=1.2, radio=2.0)
CHAFLAN = 0.3              # entrada del resalte
NERVIO = dict(radio=0.5, aprieto=0.08, por_lado_largo=3, por_lado_corto=1)


def rectangulo(largo, alto, radio):
    return CrossSection.square((largo - 2 * radio, alto - 2 * radio), center=True).offset(radio, circular_segments=48)


def construir():
    l, a = HUECO[0] - 2 * HOLGURA, HUECO[1] - 2 * HOLGURA
    p = PESTANA
    pestana = rectangulo(HUECO[0] + 2 * p["ancho"], HUECO[1] + 2 * p["ancho"], p["radio"]).extrude(p["grosor"])
    # resalte con chaflán en el frente: tramo recto y tramo que se estrecha
    recto = rectangulo(l, a, RADIO_HUECO).extrude(GROSOR - CHAFLAN + 0.01).translate((0, 0, p["grosor"] - 0.01))
    punta = Manifold.batch_hull([
        rectangulo(l, a, RADIO_HUECO).extrude(0.01).translate((0, 0, p["grosor"] + GROSOR - CHAFLAN - 0.05)),
        rectangulo(l - 2 * CHAFLAN, a - 2 * CHAFLAN, RADIO_HUECO - CHAFLAN / 2).extrude(0.01)
        .translate((0, 0, p["grosor"] + GROSOR - 0.01))])
    # nervios: medias cañas en los cantos que sobresalen HOLGURA + aprieto
    # junto a la pestaña y van menguando hasta quedar dentro del resalte en
    # el frente (rampa de entrada: aprietan poco a poco)
    n = NERVIO
    sale = HOLGURA + n["aprieto"]
    alto_nervio = GROSOR - CHAFLAN
    abajo = Manifold.cylinder(0.01, n["radio"], n["radio"], 32).translate((0, 0, p["grosor"] - 0.01))
    arriba = Manifold.cylinder(0.01, n["radio"], n["radio"], 32).translate((0, 0, p["grosor"] + alto_nervio - 0.1))

    def nervio(x, y, ux, uy):  # (ux, uy): hacia fuera del canto
        c = n["radio"] - sale
        return Manifold.batch_hull([abajo.translate((x - ux * c, y - uy * c, 0)),
                                    arriba.translate((x - ux * (c + sale + 0.05), y - uy * (c + sale + 0.05), 0))])
    nervios = []
    for x in np.linspace(-l / 2 + 12, l / 2 - 12, n["por_lado_largo"]):
        for s in (-1, 1):
            nervios.append(nervio(x, s * a / 2, 0, s))
    for s in (-1, 1):
        nervios.append(nervio(s * l / 2, 0, s, 0))
    pieza = Manifold.batch_boolean([pestana, recto, punta] + nervios, OpType.Add)
    m = pieza.to_mesh()
    return trimesh.Trimesh(m.vert_properties[:, :3], m.tri_verts, process=False)


if __name__ == "__main__":
    malla = construir()
    malla.export(pathlib.Path(__file__).with_name("ventanilla_buzon.stl"))
    print("estanca:", malla.is_watertight, "| tamaño:", np.round(malla.extents, 2), "| volumen cm3:",
          round(malla.volume / 1000, 2))
