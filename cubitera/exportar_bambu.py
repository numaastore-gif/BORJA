"""Proyecto 3MF de Bambu Studio (H2D) de la cubitera con los ajustes de
impresión ya puestos en el objeto para que salga estanca sin relleno al 100 %.
Un STL no lleva ajustes; el 3MF los guarda en Metadata/model_settings.config.

  - capa de 0,2 mm: el fondo de 2 mm son justo 10 capas
  - 5 capas inferiores + 5 superiores: el fondo sale entero macizo, también
    debajo del tope (que es hueco y apoya en el fondo)
  - 4 perímetros: la pared de 3 mm sale entera de perímetros, sin relleno
  - relleno al 15 %: con lo anterior no queda sitio donde ponerlo

    python cubitera.py          # genera cubitera.stl
    python exportar_bambu.py    # crea cubitera_H2D.3mf
"""
import pathlib
import zipfile

import trimesh

AQUI = pathlib.Path(__file__).parent
DESTINO = AQUI / "cubitera_H2D.3mf"
CAMA = (350.0, 320.0)  # Bambu Lab H2D
NOMBRE = "cubitera"
AJUSTES = {
    "layer_height": "0.2",
    "bottom_shell_layers": "5",
    "top_shell_layers": "5",
    "bottom_shell_thickness": "0",   # que mande el número de capas
    "top_shell_thickness": "0",
    "wall_loops": "4",
    "sparse_infill_density": "15%",
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


def exportar():
    m = trimesh.load(AQUI / "cubitera.stl")
    c = (m.bounds[0] + m.bounds[1]) / 2
    m.apply_translation([-c[0], -c[1], -m.bounds[0][2]])  # centrada y apoyada en la cama
    v = "\n".join(f'<vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in m.vertices)
    t = "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
    modelo = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
              'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
              ' <metadata name="Application">BambuStudio-01.10.00.00</metadata>\n'
              ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
              ' <metadata name="Title">Cubitera Valle y Jose</metadata>\n'
              f' <resources>\n  <object id="1" type="model" name="{NOMBRE}">\n'
              f'<mesh><vertices>\n{v}\n</vertices><triangles>\n{t}\n</triangles></mesh>\n  </object>\n'
              ' </resources>\n <build>\n'
              f'  <item objectid="1" transform="1 0 0 0 1 0 0 0 1 {CAMA[0] / 2} {CAMA[1] / 2} 0" printable="1"/>\n'
              ' </build>\n</model>\n')
    extra = "\n".join(f'    <metadata key="{k}" value="{v}"/>' for k, v in AJUSTES.items())
    config = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="1">
    <metadata key="name" value="{NOMBRE}"/>
    <metadata key="extruder" value="1"/>
{extra}
    <part id="1" subtype="normal_part">
      <metadata key="name" value="{NOMBRE}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
    </part>
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value="Cubitera"/>
    <metadata key="locked" value="false"/>
    <model_instance>
      <metadata key="object_id" value="1"/>
      <metadata key="instance_id" value="0"/>
    </model_instance>
  </plate>
</config>
"""
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", TIPOS)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", modelo)
        z.writestr("Metadata/model_settings.config", config)
    return m


if __name__ == "__main__":
    m = exportar()
    print(DESTINO.name, round(DESTINO.stat().st_size / 1e6, 1), "MB | estanca:", m.is_watertight,
          "| tamaño:", m.extents.round(1))
