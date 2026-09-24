"""Soporte para papelera, según el croquis (croquis.png), sin ruedas.

Bandeja rectangular: exterior 380 x 300 mm, hueco de 340 x 260 mm donde encaja
la papelera (marco de 20 mm por lado), fondo macizo y laterales alrededor.
Como entera no cabe en la Bambu Lab H2D (325 x 320 x 325 mm), se parte por la
mitad del largo en dos piezas unidas por dos colas de milano verticales en el
fondo: se encajan deslizando una sobre otra de arriba abajo y se pegan
(también los laterales, que van a tope). El modelo es macizo: para que salga
relleno del todo, imprimir con relleno al 100 %.
Primer modelo: las alturas no vienen en el croquis y son una propuesta.
Por debajo lleva una rosca M5 cerca de cada esquina, metida bajo el hueco
(por eso el fondo es grueso), para roscar las bolas de apoyo al suelo.

    pip install numpy trimesh manifold3d
    python soporte.py
"""
import pathlib

import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, JoinType, Manifold

EXTERIOR = (380.0, 300.0)   # medidas del cliente
INTERIOR = (340.0, 260.0)
FONDO = 14.0          # grosor del fondo: aloja las roscas, que van bajo el hueco
BORDE = 60.0          # altura de los laterales por encima del fondo
# Unión de las dos piezas: colas de milano (centro en y, cuello, cabeza, fondo)
# Dos colas en el fondo; los laterales van a tope y se pegan.
COLAS = [(-65.0, 30.0, 44.0, 20.0),
         (65.0, 30.0, 44.0, 20.0)]
HOLGURA_UNION = 0.15  # mm que se retira cada pieza en la unión para que encaje
RADIO_EXT = 15.0      # esquinas redondeadas por fuera
RADIO_INT = 8.0       # y por dentro (la papelera suele tener esquinas curvas)
CHAFLAN = 2.0         # chaflán en los cantos de arriba y de abajo
# Roscas M5 x 0,8 a derechas, abiertas por abajo, una por esquina
ROSCA = dict(diametro=5.0, paso=0.8, profundidad=12.0,
             holgura=0.3,       # mm de más en diámetro: el plástico impreso encoge
             avellanado=0.8)    # chaflán de entrada para que el tornillo entre recto
ROSCA_DESDE_BORDE = 40.0  # centro de la rosca: 20 mm hacia dentro del hueco


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


def rosca_hembra():
    """Macho de corte con el perfil métrico (60°) para vaciar una rosca
    interior. Su sección es una leva cuyo radio sigue el perfil del filete;
    al extruirla girando 360° por paso sale la hélice a derechas."""
    r = ROSCA
    p, h = r["paso"], r["profundidad"]
    r_may = (r["diametro"] + r["holgura"]) / 2
    r_men = r_may - 0.541 * p  # profundidad de filete de una rosca interior ISO
    t = np.linspace(0, 1, 49)[:-1]  # 7,5° por punto: de sobra para imprimir
    tri = 1 - np.abs(2 * t - 1)                 # 0 en el fondo, 1 en la cresta
    perfil = np.clip((tri - 0.125) / 0.75, 0, 1)  # crestas y fondos planos
    ang = -2 * np.pi * t
    radio = r_men + (r_may - r_men) * perfil
    seccion = CrossSection([np.c_[radio * np.cos(ang), radio * np.sin(ang)]], FillRule.EvenOdd)
    vueltas = (h + p) / p
    macho = seccion.extrude(h + p, n_divisions=int(vueltas * 16), twist_degrees=360 * vueltas) \
        .translate((0, 0, -p))
    a = r["avellanado"]
    entrada = Manifold.cylinder(a + 0.01, r_may + a, r_may, 64).translate((0, 0, -0.005))
    return macho + entrada


def construir():
    alto = FONDO + BORDE
    cuerpo = bloque(*EXTERIOR, RADIO_EXT, alto, CHAFLAN)
    hueco = rectangulo(*INTERIOR, RADIO_INT).extrude(BORDE + 1).translate((0, 0, FONDO))
    macho = rosca_hembra()
    dx = EXTERIOR[0] / 2 - ROSCA_DESDE_BORDE
    dy = EXTERIOR[1] / 2 - ROSCA_DESDE_BORDE
    roscas = Manifold.compose([macho.translate((sx * dx, sy * dy, 0))
                               for sx in (-1, 1) for sy in (-1, 1)])
    return cuerpo - hueco - roscas


def linea_de_union():
    """Línea de corte en x = 0 con las colas de milano (salen hacia +x)."""
    pts = [(0.0, -1000.0)]
    for y, cuello, cabeza, fondo in COLAS:
        pts += [(0.0, y - cuello / 2), (fondo, y - cabeza / 2), (fondo, y + cabeza / 2), (0.0, y + cuello / 2)]
    return pts + [(0.0, 1000.0)]


def piezas():
    """Las dos mitades: la 1 (x < 0) lleva las colas, la 2 las hembras."""
    linea = linea_de_union()
    izq = CrossSection([np.array(linea + [(-1000.0, 1000.0), (-1000.0, -1000.0)])], FillRule.EvenOdd)
    der = CrossSection([np.array(linea + [(1000.0, 1000.0), (1000.0, -1000.0)])], FillRule.EvenOdd)
    todo = construir()
    alto = FONDO + BORDE + 2
    corta = lambda region: region.offset(-HOLGURA_UNION, JoinType.Miter).extrude(alto).translate((0, 0, -1))
    return todo ^ corta(izq), todo ^ corta(der)


def a_trimesh(m):
    s = m.to_mesh()
    return trimesh.Trimesh(s.vert_properties[:, :3], s.tri_verts, process=False)


if __name__ == "__main__":
    aqui = pathlib.Path(__file__).parent
    for i, p in enumerate(piezas(), 1):
        t = a_trimesh(p)
        t.export(aqui / f"soporte_pieza_{i}.stl")
        print(f"pieza {i}: estanca={t.is_watertight} tamaño mm={np.round(t.extents, 1)} "
              f"volumen cm3={round(t.volume / 1000)}")
