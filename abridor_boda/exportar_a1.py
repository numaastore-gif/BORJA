"""Proyectos 3MF del abridor y del espejo para la Bambu Lab A1 con boquilla de
0,2 mm, con los ajustes con los que el dibujo salió bien impreso.

Usa como plantilla el propio proyecto que funcionó (plantilla_A1_0.2.3mf,
guardado desde Bambu Studio: A1 0,2 mm, capa 0,1 mm, primera capa de 0,25 mm a
16 mm/s, piel difusa, placa texturizada) y solo cambia las mallas de sus dos
piezas (disco y dibujo) y los nombres. Todos los ajustes quedan tal cual.

    python abridor.py && python espejo.py
    python exportar_a1.py        # crea abridor_boda_A1.3mf y espejo_boda_A1.3mf
"""
import pathlib
import re
import zipfile

import numpy as np
import trimesh

AQUI = pathlib.Path(__file__).parent
PLANTILLA = AQUI / "plantilla_A1_0.2.3mf"
PROYECTOS = {
    "abridor_boda_A1.3mf": ("Abridor boda", "abridor_placa.stl", "abridor_dibujo.stl"),
    "espejo_boda_A1.3mf": ("Espejo boda", "espejo_disco.stl", "espejo_dibujo.stl"),
}


def num(x):
    return f"{x:.9g}"


def objeto(i, uuid, m):
    v = "\n".join(f'     <vertex x="{num(a)}" y="{num(b)}" z="{num(c)}"/>' for a, b, c in m.vertices)
    t = "\n".join(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in m.faces)
    return (f'  <object id="{i}" p:UUID="{uuid}" type="model">\n   <mesh>\n    <vertices>\n{v}\n    </vertices>\n'
            f'    <triangles>\n{t}\n    </triangles>\n   </mesh>\n  </object>')


def exportar(destino, nombre, piezas):
    z = zipfile.ZipFile(PLANTILLA)
    sub = z.read("3D/Objects/object_1.model").decode()
    principal = z.read("3D/3dmodel.model").decode()
    ajustes = z.read("Metadata/model_settings.config").decode()
    uuids = re.findall(r'<object id="\d+" p:UUID="([^"]+)"', sub)
    objetos, offs, caras = [], [], []
    for i, (f, uuid) in enumerate(zip(piezas, uuids), 1):
        m = trimesh.load(AQUI / f)
        o = (m.bounds[0] + m.bounds[1]) / 2          # Bambu guarda cada pieza centrada en su caja
        m.apply_translation(-o)
        objetos.append(objeto(i, uuid, m))
        offs.append(o)
        caras.append(len(m.faces))
    cab = sub[:sub.index("<resources>") + len("<resources>")]
    pie = sub[sub.index("</resources>"):]
    sub = cab + "\n" + "\n".join(objetos) + "\n " + pie
    # transformaciones de las piezas en el modelo principal y en los ajustes
    comps = re.findall(r'<component [^>]*/>', principal)
    for c, o in zip(comps, offs):
        principal = principal.replace(c, re.sub(r'transform="[^"]+"', f'transform="1 0 0 0 1 0 0 0 1 {num(o[0])} {num(o[1])} {num(o[2])}"', c))
    principal = re.sub(r'<metadata name="Title">[^<]*</metadata>', f'<metadata name="Title">{nombre}</metadata>', principal)
    partes = re.findall(r'<part id="\d+".*?</part>', ajustes, re.S)
    for p, o, n in zip(partes, offs, caras):
        q = re.sub(r'key="matrix" value="[^"]+"', f'key="matrix" value="1 0 0 {num(o[0])} 0 1 0 {num(o[1])} 0 0 1 {num(o[2])} 0 0 0 1"', p)
        for eje, val in zip("xyz", o):
            q = re.sub(rf'key="source_offset_{eje}" value="[^"]+"', f'key="source_offset_{eje}" value="{num(val)}"', q)
        q = re.sub(r'mesh_stat face_count="\d+"', f'mesh_stat face_count="{n}"', q)
        ajustes = ajustes.replace(p, q)
    vols = re.findall(r'<assemble_item object_id="\d+" volume_id="\d+" transform="[^"]+" />', ajustes)
    for v, o in zip(vols, offs):
        ajustes = ajustes.replace(v, re.sub(r'transform="[^"]+"', f'transform="1 0 0 0 1 0 0 0 1 {num(o[0])} {num(o[1])} {num(o[2])}"', v))
    ajustes = re.sub(r'<metadata face_count="\d+"/>', f'<metadata face_count="{sum(caras)}"/>', ajustes)
    ajustes = re.sub(r'(<object id="\d+">\s*<metadata key="name" value=")[^"]+"', rf'\g<1>{nombre}"', ajustes)
    ajustes = re.sub(r'key="plater_name" value="[^"]*"', f'key="plater_name" value="{nombre}"', ajustes)
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as w:
        for item in z.infolist():
            datos = {"3D/Objects/object_1.model": sub, "3D/3dmodel.model": principal,
                     "Metadata/model_settings.config": ajustes}.get(item.filename)
            w.writestr(item.filename, datos.encode() if datos is not None else z.read(item.filename))
    return caras


if __name__ == "__main__":
    for destino, (nombre, disco, dibujo) in PROYECTOS.items():
        caras = exportar(AQUI / destino, nombre, (disco, dibujo))
        print(destino, caras, round((AQUI / destino).stat().st_size / 1e6, 2), "MB")
