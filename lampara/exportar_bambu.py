"""Proyecto 3MF de Bambu Studio para la Bambu Lab H2D con las piezas de la
lámpara repartidas en camas, como en el proyecto de referencia:

  cama 1   base y remate
  cama 2-4 cuatro rodajas cada una
  cama 5   las dos últimas rodajas
  cama 6   difusor (aparte: va en filamento translúcido)

Las camas se colocan como las ordena Bambu Studio (en columnas, separadas un
20 % del tamaño de la cama) y cada objeto va centrado en su hueco. Con la
textura a resolución de impresión un solo proyecto pasa de 30 MB, así que se
reparte en dos ficheros: _1 con base, remate y difusor (camas 1 y 6) y _2
con las rodajas (camas 2-5). Cada cama conserva su número en el nombre.

    python lampara.py            # genera las piezas en piezas/
    python exportar_bambu.py     # crea lampara_numa_home_H2D_1.3mf y _2.3mf
"""
import pathlib
import zipfile

import numpy as np
import trimesh

AQUI = pathlib.Path(__file__).parent
CAMA = (350.0, 320.0)
HUECO_CAMAS = 1 / 5
# fichero -> camas que lleva
FICHEROS = {"lampara_numa_home_H2D_1.3mf": (1, 6), "lampara_numa_home_H2D_2.3mf": (2, 3, 4, 5)}

# (cama, pieza, posición del centro respecto al centro de la cama)
CUATRO = [(-77, 70), (77, 70), (-77, -70), (77, -70)]
PROYECTO = [(1, "base", (-80, 0)), (1, "remate", (95, 0))]
for i in range(14):
    PROYECTO.append((2 + i // 4, f"rodaja_{i + 1:02d}", CUATRO[i % 4]))
PROYECTO.append((6, "difusor", (0, 0)))

TIPOS = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="config" ContentType="text/xml"/>
</Types>
"""
RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""


def origen_cama(n, total):
    columnas = int(np.ceil(np.sqrt(total)))
    fila, col = divmod(n - 1, columnas)
    return col * CAMA[0] * (1 + HUECO_CAMAS), -fila * CAMA[1] * (1 + HUECO_CAMAS)


def num(x):
    """Coordenada a 0,0001 mm sin ceros sobrantes, para que el 3MF pese menos."""
    return f"{x:.4f}".rstrip("0").rstrip(".")


def xml_malla(m):
    # a 0,0001 mm no se funden vértices distintos (la malla va a 0,25 mm)
    assert len(np.unique(np.round(m.vertices, 4), axis=0)) == len(m.vertices)
    v = "\n".join(f'<vertex x="{num(x)}" y="{num(y)}" z="{num(z)}"/>' for x, y, z in m.vertices)
    t = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
    return f"<mesh><vertices>\n{v}\n</vertices><triangles>\n{t}\n</triangles></mesh>"


def exportar(destino, camas):
    proyecto = [p for p in PROYECTO if p[0] in camas]
    orden = {c: n for n, c in enumerate(camas, 1)}  # posición de la cama en este fichero
    objetos, items, config, huellas = [], [], [], {}
    for i, (cama, nombre, (dx, dy)) in enumerate(proyecto, 1):
        m = trimesh.load(AQUI / "piezas" / f"{nombre}.stl")
        c = (m.bounds[0] + m.bounds[1]) / 2
        m.apply_translation([-c[0], -c[1], -m.bounds[0][2]])  # centrada y apoyada en la cama
        objetos.append(f'  <object id="{i}" type="model" name="{nombre}">\n{xml_malla(m)}\n  </object>')
        ox, oy = origen_cama(orden[cama], len(camas))
        x, y = ox + CAMA[0] / 2 + dx, oy + CAMA[1] / 2 + dy
        items.append(f'  <item objectid="{i}" transform="1 0 0 0 1 0 0 0 1 {x:.4f} {y:.3f} 0" printable="1"/>')
        config.append(f"""  <object id="{i}">
    <metadata key="name" value="{nombre}"/>
    <metadata key="extruder" value="1"/>
    <part id="1" subtype="normal_part">
      <metadata key="name" value="{nombre}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
    </part>
  </object>""")
        huellas.setdefault(cama, []).append((nombre, x - ox - m.extents[0] / 2, y - oy - m.extents[1] / 2,
                                            x - ox + m.extents[0] / 2, y - oy + m.extents[1] / 2, m.extents[2]))
    for cama in camas:
        inst = "\n".join(f"""    <model_instance>
      <metadata key="object_id" value="{i}"/>
      <metadata key="instance_id" value="0"/>
    </model_instance>""" for i, (c, _, _) in enumerate(proyecto, 1) if c == cama)
        config.append(f"""  <plate>
    <metadata key="plater_id" value="{orden[cama]}"/>
    <metadata key="plater_name" value="Cama {cama}"/>
    <metadata key="locked" value="false"/>
{inst}
  </plate>""")
    modelo = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
              'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
              ' <metadata name="Application">BambuStudio-01.10.00.00</metadata>\n'
              ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
              ' <metadata name="Title">Lámpara tronco numa home</metadata>\n'
              ' <resources>\n' + "\n".join(objetos) + '\n </resources>\n <build>\n'
              + "\n".join(items) + '\n </build>\n</model>\n')
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", TIPOS)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", modelo)
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(config) + "\n</config>\n")
    return huellas


if __name__ == "__main__":
    for fichero, camas in FICHEROS.items():
        destino = AQUI / fichero
        huellas = exportar(destino, camas)
        for cama, lista in sorted(huellas.items()):
            for nombre, x0, y0, x1, y1, h in lista:
                fuera = x0 < 0 or y0 < 0 or x1 > CAMA[0] or y1 > CAMA[1]
                print(f"cama {cama}: {nombre:10s} x {x0:6.1f}–{x1:6.1f}  y {y0:6.1f}–{y1:6.1f}  alto {h:5.1f}"
                      + ("  ¡FUERA DE LA CAMA!" if fuera else ""))
        print(destino.name, round(destino.stat().st_size / 1e6, 1), "MB")
