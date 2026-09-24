"""Exporta cada pieza del soporte como proyecto 3MF para Bambu Studio con el
relleno al 100 % ya puesto en el objeto (un STL no puede llevar ajustes de
impresión y Bambu Studio usa por defecto un 15 % de relleno).

El ajuste va en Metadata/model_settings.config, que es donde Bambu Studio
guarda los ajustes propios de cada objeto.

    python exportar_bambu.py
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
    v = "\n".join(f'     <vertex x="{x:.5f}" y="{y:.5f}" z="{z:.5f}"/>' for x, y, z in malla.vertices)
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


if __name__ == "__main__":
    for n in PIEZAS:
        destino, malla = exportar(n)
        print(f"{destino.name}: {len(malla.faces)} triángulos, estanca={malla.is_watertight}, "
              f"{np.round(malla.extents, 1)} mm")
