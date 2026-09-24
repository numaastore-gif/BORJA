"""Exporta cada pieza del soporte como proyecto 3MF para Bambu Studio con el
relleno al 100 % ya puesto en el objeto (un STL no puede llevar ajustes de
impresión y Bambu Studio usa por defecto un 15 % de relleno).

El ajuste va en Metadata/model_settings.config, que es donde Bambu Studio
guarda los ajustes propios de cada objeto.

    python exportar_bambu.py

También genera soporte_papelera_H2D.3mf: un único proyecto con tres camas
(pieza 1, pieza 2, y bolas + espárragos), colocadas como las ordena Bambu
Studio: en columnas, separadas un 20 % del tamaño de la cama.
"""
import pathlib
import zipfile

import numpy as np
import trimesh

AQUI = pathlib.Path(__file__).parent
PIEZAS = ["soporte_pieza_1", "soporte_pieza_2", "bolas", "esparragos"]
AJUSTES = {
    "sparse_infill_density": "100%",
    "sparse_infill_pattern": "zig-zag",   # relleno macizo, en líneas alternas
    "wall_loops": "3",
}

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


def modelo(malla, nombre):
    v = "\n".join(f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in malla.vertices)
    t = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in malla.faces)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
 <metadata name="Application">soporte-papelera</metadata>
 <resources>
  <object id="1" type="model" name="{nombre}">
   <mesh>
    <vertices>
{v}
    </vertices>
    <triangles>
{t}
    </triangles>
   </mesh>
  </object>
 </resources>
 <build>
  <item objectid="1" printable="1"/>
 </build>
</model>
"""


def ajustes(nombre, caras):
    extra = "\n".join(f'    <metadata key="{k}" value="{v}"/>' for k, v in AJUSTES.items())
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="1">
    <metadata key="name" value="{nombre}"/>
    <metadata key="extruder" value="1"/>
{extra}
    <part id="1" subtype="normal_part">
      <metadata key="name" value="{nombre}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>
  </object>
</config>
"""


def exportar(nombre):
    malla = trimesh.load(AQUI / f"{nombre}.stl")
    malla.merge_vertices()
    malla.apply_translation([-malla.bounds[0][0] - malla.extents[0] / 2,
                             -malla.bounds[0][1] - malla.extents[1] / 2, -malla.bounds[0][2]])
    destino = AQUI / f"{nombre}_relleno100.3mf"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", TIPOS)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", modelo(malla, nombre))
        z.writestr("Metadata/model_settings.config", ajustes(nombre, len(malla.faces)))
    return destino, malla


CAMA = (350.0, 320.0)   # cama de la Bambu Lab H2D
HUECO_CAMAS = 1 / 5     # separación entre camas que usa Bambu Studio
# (cama, nombre del STL, desplazamiento dentro de la cama)
PROYECTO = [(1, "soporte_pieza_1", (0, 0)),
            (2, "soporte_pieza_2", (0, 0)),
            (3, "bolas", (-40, 0)),
            (3, "esparragos", (75, 0))]


def origen_cama(n, total):
    columnas = int(np.ceil(np.sqrt(total)))
    fila, col = divmod(n - 1, columnas)
    return col * CAMA[0] * (1 + HUECO_CAMAS), -fila * CAMA[1] * (1 + HUECO_CAMAS)


def exportar_proyecto(destino):
    camas = sorted({c for c, _, _ in PROYECTO})
    objetos, items, config = [], [], []
    extra = "\n".join(f'    <metadata key="{k}" value="{v}"/>' for k, v in AJUSTES.items())
    for i, (cama, nombre, (dx, dy)) in enumerate(PROYECTO, 1):
        malla = trimesh.load(AQUI / f"{nombre}.stl")
        malla.merge_vertices()
        # centrado en su propio origen, apoyado en z = 0
        malla.apply_translation([-(malla.bounds[0][0] + malla.bounds[1][0]) / 2,
                                 -(malla.bounds[0][1] + malla.bounds[1][1]) / 2, -malla.bounds[0][2]])
        v = "\n".join(f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in malla.vertices)
        t = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in malla.faces)
        objetos.append(f'  <object id="{i}" type="model" name="{nombre}">\n   <mesh>\n    <vertices>\n{v}\n'
                       f'    </vertices>\n    <triangles>\n{t}\n    </triangles>\n   </mesh>\n  </object>')
        ox, oy = origen_cama(cama, len(camas))
        x, y = ox + CAMA[0] / 2 + dx, oy + CAMA[1] / 2 + dy
        items.append(f'  <item objectid="{i}" transform="1 0 0 0 1 0 0 0 1 {x:.3f} {y:.3f} 0" printable="1"/>')
        config.append(f"""  <object id="{i}">
    <metadata key="name" value="{nombre}"/>
    <metadata key="extruder" value="1"/>
{extra}
    <part id="1" subtype="normal_part">
      <metadata key="name" value="{nombre}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
    </part>
  </object>""")
    for cama in camas:
        instancias = "\n".join(f"""    <model_instance>
      <metadata key="object_id" value="{i}"/>
      <metadata key="instance_id" value="0"/>
    </model_instance>""" for i, (c, _, _) in enumerate(PROYECTO, 1) if c == cama)
        config.append(f"""  <plate>
    <metadata key="plater_id" value="{cama}"/>
    <metadata key="plater_name" value="Cama {cama}"/>
    <metadata key="locked" value="false"/>
{instancias}
  </plate>""")
    modelo_xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                  '<model unit="millimeter" xml:lang="en-US" '
                  'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
                  ' <metadata name="Application">BambuStudio-01.10.00.00</metadata>\n'
                  ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
                  ' <metadata name="Title">Soporte papelera</metadata>\n'
                  ' <resources>\n' + "\n".join(objetos) + '\n </resources>\n <build>\n'
                  + "\n".join(items) + '\n </build>\n</model>\n')
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", TIPOS)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", modelo_xml)
        z.writestr("Metadata/model_settings.config",
                   '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(config) + "\n</config>\n")


if __name__ == "__main__":
    exportar_proyecto(AQUI / "soporte_papelera_H2D.3mf")
    print("soporte_papelera_H2D.3mf: 3 camas")
    for n in PIEZAS:
        destino, malla = exportar(n)
        print(f"{destino.name}: {len(malla.faces)} triángulos, estanca={malla.is_watertight}, "
              f"{np.round(malla.extents, 1)} mm")
