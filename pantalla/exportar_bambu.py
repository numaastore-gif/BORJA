"""Proyecto 3MF de Bambu Studio para la H2D con la pantalla lista para
imprimir en modo jarrón con piel difusa. El formato y la configuración
completa salen de la plantilla de un proyecto real de H2D
(../cubitera/plantilla_H2D_project_settings.config); aquí solo se cambia:

  - modo jarrón (espiral), del revés: 8 capas inferiores macizas (el disco de
    arriba de la pantalla, con el agujero del E27) y luego una sola pared
    abierta por la boca
  - pared de 0,6 mm de ancho de línea (más resistente y más difusora)
  - piel difusa en la pared exterior, 0,3 mm de grosor
  - un solo filamento (blanco)

    python pantalla.py          # genera pantalla_jarron.stl
    python exportar_bambu.py    # crea pantalla_jarron_H2D.3mf
"""
import json
import pathlib
import zipfile

import trimesh

AQUI = pathlib.Path(__file__).parent
DESTINO = AQUI / "pantalla_jarron_H2D.3mf"
PLANTILLA = AQUI.parent / "cubitera" / "plantilla_H2D_project_settings.config"
VERSION = "02.00.02.01"  # la de la plantilla
CAMA = (350.0, 320.0)
NOMBRE = "Pantalla jarrón E27"
PARTES = [("pantalla", "pantalla_jarron.stl", 1)]
COLORES = ["#FFFFFF"]  # blanco
AJUSTES = {"spiral_mode": "1", "spiral_mode_smooth": "1", "bottom_shell_layers": "8", "top_shell_layers": "0",
           "wall_loops": "1", "sparse_infill_density": "0%", "outer_wall_line_width": "0.6",
           "fuzzy_skin": "external", "fuzzy_skin_thickness": "0.3", "fuzzy_skin_point_distance": "0.8",
           "layer_height": "0.2", "initial_layer_print_height": "0.2"}

NS = ('xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
      'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
      'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p"')
TIPOS = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="png" ContentType="image/png"/>
 <Default Extension="gcode" ContentType="text/x.gcode"/>
</Types>
"""
RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
RELS_MODELO = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/Objects/object_1.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>
"""
SLICE_INFO = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <header>
    <header_item key="X-BBL-Client-Type" value="slicer"/>
    <header_item key="X-BBL-Client-Version" value="{VERSION}"/>
  </header>
</config>
"""


def configuracion():
    """Configuración del proyecto: la plantilla con un filamento y los ajustes de jarrón."""
    d = json.load(open(PLANTILLA))
    n = len(d["filament_settings_id"])  # 8 en la plantilla
    for k, v in list(d.items()):
        if not isinstance(v, list):
            continue
        if len(v) == n:  # un valor por filamento
            d[k] = v[:1]
        elif len(v) == 2 * n and k.startswith(("filament_", "nozzle_temperature", "flush_volumes_vector")):
            d[k] = v[:2]  # un valor por filamento y variante de boquilla
    bloques = len(d["flush_volumes_matrix"]) // (n * n)
    d["flush_volumes_matrix"] = ["0"] * bloques
    d["filament_colour"] = COLORES
    d["filament_map"] = ["1"]
    d.update(AJUSTES)
    d["different_settings_to_system"] = [";".join(sorted(set(AJUSTES) | {"wall_generator", "enable_prime_tower"})), "", ""]
    d["enable_prime_tower"] = "0"
    return json.dumps(d, indent=4, ensure_ascii=False)


def malla_xml(i, m, uuid):
    v = "\n".join(f'     <vertex x="{x:.6f}" y="{y:.6f}" z="{z:.6f}"/>' for x, y, z in m.vertices)
    t = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
    return (f'  <object id="{i}" p:UUID="{uuid}" type="model">\n   <mesh>\n    <vertices>\n{v}\n    </vertices>\n'
            f'    <triangles>\n{t}\n    </triangles>\n   </mesh>\n  </object>')


def exportar():
    mallas = [trimesh.load(AQUI / f) for _, f, _ in PARTES]
    caja = trimesh.util.concatenate(mallas).bounds
    centro = (caja[0] + caja[1]) / 2
    for m in mallas:  # centradas juntas y apoyadas en la cama
        m.apply_translation([-centro[0], -centro[1], -caja[0][2]])
    objetos = "\n".join(malla_xml(i, m, f"000{i}0000-81cb-4c03-9d28-80fed5dfa1dc")
                        for i, m in enumerate(mallas, 1))
    sub = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n'
           f' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n{objetos}\n </resources>\n <build/>\n</model>\n')
    comp = "\n".join(f'    <component p:path="/3D/Objects/object_1.model" objectid="{i}" '
                     f'p:UUID="0001000{i - 1}-b206-40ff-9872-83e8017abed1" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
                     for i in range(1, len(mallas) + 1))
    oid = len(mallas) + 1
    x, y = CAMA[0] / 2, CAMA[1] / 2
    meta = {"Application": f"BambuStudio-{VERSION}", "BambuStudio:3mfVersion": "1", "Copyright": "",
            "CreationDate": "2026-09-26", "Description": "", "Designer": "numashome", "License": "",
            "ModificationDate": "2026-09-26", "Origin": "", "Title": NOMBRE}
    principal = (f'<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" {NS}>\n'
                 + "".join(f' <metadata name="{k}">{v}</metadata>\n' for k, v in meta.items())
                 + f' <resources>\n  <object id="{oid}" p:UUID="00000001-61cb-4c03-9d28-80fed5dfa1dc" type="model">\n'
                 f'   <components>\n{comp}\n   </components>\n  </object>\n </resources>\n'
                 f' <build p:UUID="2c7c17d8-22b5-4d84-8835-1976022ea369">\n'
                 f'  <item objectid="{oid}" p:UUID="00000002-b1ec-4553-aec9-835e5b724bb4" '
                 f'transform="1 0 0 0 1 0 0 0 1 {x} {y} 0" printable="1"/>\n </build>\n</model>\n')
    # en el objeto solo los ajustes que admite por pieza (el modo jarrón es del proyecto)
    globales = {"spiral_mode", "spiral_mode_smooth", "initial_layer_print_height"}
    ajustes = "\n".join(f'    <metadata key="{k}" value="{v}"/>' for k, v in AJUSTES.items() if k not in globales)
    partes = "\n".join(f"""    <part id="{i}" subtype="normal_part">
      <metadata key="name" value="{nombre}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="extruder" value="{filamento}"/>
      <mesh_stat face_count="{len(m.faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>""" for i, ((nombre, _, filamento), m) in enumerate(zip(PARTES, mallas), 1))
    ajustes_modelo = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="{oid}">
    <metadata key="name" value="{NOMBRE}"/>
    <metadata key="extruder" value="1"/>
{ajustes}
    <metadata face_count="{sum(len(m.faces) for m in mallas)}"/>
{partes}
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value="Cubitera"/>
    <metadata key="locked" value="false"/>
    <metadata key="filament_map_mode" value="Auto For Flush"/>
    <metadata key="filament_maps" value="1"/>
    <model_instance>
      <metadata key="object_id" value="{oid}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="101"/>
    </model_instance>
  </plate>
  <assemble>
   <assemble_item object_id="{oid}" instance_id="0" transform="1 0 0 0 1 0 0 0 1 {x} {y} 0" offset="0 0 0" />
  </assemble>
</config>
"""
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr("[Content_Types].xml", TIPOS)
        z.writestr("_rels/.rels", RELS)
        z.writestr("3D/3dmodel.model", principal)
        z.writestr("3D/_rels/3dmodel.model.rels", RELS_MODELO)
        z.writestr("3D/Objects/object_1.model", sub)
        z.writestr("Metadata/model_settings.config", ajustes_modelo)
        z.writestr("Metadata/project_settings.config", configuracion())
        z.writestr("Metadata/slice_info.config", SLICE_INFO)
    return mallas


if __name__ == "__main__":
    mallas = exportar()
    for (nombre, _, f), m in zip(PARTES, mallas):
        print(f"{nombre}: filamento {f}, estanca={m.is_watertight}, {len(m.faces)} triángulos")
    print(DESTINO.name, round(DESTINO.stat().st_size / 1e6, 1), "MB")
