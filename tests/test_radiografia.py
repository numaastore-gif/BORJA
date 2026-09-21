"""Pruebas del resumen ligero de un proyecto."""

import json
import zipfile

import pytest

from guardias.radiografia import a_markdown, radiografiar


def asc(nombre, direccion, tipo, comentario):
    return "126," + nombre.ljust(24) + direccion.ljust(12) + tipo.ljust(10) + comentario.ljust(80)


CONTENIDO = {
    "AS01_Dosificado/Dosificado.s7p": "",
    "AS01_Dosificado/simbolos.asc": "\n".join(
        [
            asc("Dos_Harina_M1", "E      0.0", "BOOL", "Marcha dosificador harina 1"),
            asc("Bas_Harina_PV", "DB12.DBD 4", "REAL", "Peso báscula harina 1"),
        ]
    ),
    "AS01_Dosificado/SCL/FB_Dosificador.scl": "FUNCTION_BLOCK",
    "AS01_Dosificado/CFC/harinas.cfc": "binario",
    "OS01_Servidor/mensajes.csv": "Number;Message text;Klasse\n"
    + "\n".join(f"{4700 + i};Mensaje {i};Alarm" for i in range(10)),
    "OS01_Servidor/leeme.txt": "notas sueltas\nsin códigos\nde mensaje\nni nada\nparecido\n",
    "OS01_Servidor/PDL/pantalla_01.pdl": "binario",
}


@pytest.fixture()
def archivado(tmp_path):
    ruta = tmp_path / "Dosificado_C700_20260918.zap17"
    with zipfile.ZipFile(ruta, "w") as z:
        for nombre, contenido in CONTENIDO.items():
            z.writestr(nombre, contenido)
    return ruta


@pytest.fixture()
def carpeta(tmp_path):
    raiz = tmp_path / "extraido"
    for nombre, contenido in CONTENIDO.items():
        destino = raiz / nombre
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(contenido)
    return raiz


def test_radiografia_de_un_archivado(archivado):
    r = radiografiar(archivado)

    assert r["version_deducida"] == "TIA Portal V17"
    assert r["estaciones"] == ["AS01_Dosificado", "OS01_Servidor"]
    assert r["proyectos_step7"] == ["AS01_Dosificado/Dosificado.s7p"]
    assert r["ficheros"] == len(CONTENIDO)
    assert r["extensiones"][".pdl"] == 1

    (tabla,) = r["tablas_simbolos"]
    assert tabla["simbolos"] == 2
    assert tabla["muestra"][0]["nombre"] == "Dos_Harina_M1"

    (lista,) = r["listas_mensajes"]
    assert lista["alarmas"] == 10

    assert r["total_bloques"] == 2
    assert r["total_pantallas"] == 1


def test_una_carpeta_extraida_da_el_mismo_contenido(archivado, carpeta):
    del_zip = radiografiar(archivado)
    de_carpeta = radiografiar(carpeta)

    assert de_carpeta["tipo"] == "carpeta"
    assert de_carpeta["estaciones"] == del_zip["estaciones"]
    assert de_carpeta["extensiones"] == del_zip["extensiones"]
    assert [t["simbolos"] for t in de_carpeta["tablas_simbolos"]] == [2]


def test_un_txt_cualquiera_no_cuela_como_lista_de_mensajes(archivado):
    rutas = [m["ruta"] for m in radiografiar(archivado)["listas_mensajes"]]
    assert "OS01_Servidor/leeme.txt" not in rutas


def test_las_listas_largas_se_recortan(tmp_path):
    ruta = tmp_path / "grande.zip"
    with zipfile.ZipFile(ruta, "w") as z:
        for i in range(200):
            z.writestr(f"OS01/PDL/pantalla_{i:03}.pdl", "x")

    r = radiografiar(ruta, muestra=5)
    assert r["total_pantallas"] == 200
    assert len(r["pantallas"]) == 20          # muestra * 4


def test_el_resultado_es_pequeno_y_serializable(archivado):
    r = radiografiar(archivado, muestra=15)
    texto = json.dumps(r, ensure_ascii=False)
    assert len(texto) < 100_000               # cabe en un mensaje
    assert "Dos_Harina_M1" in texto


def test_markdown_incluye_lo_importante(archivado):
    md = a_markdown(radiografiar(archivado))
    assert "# Radiografía de Dosificado_C700_20260918.zap17" in md
    assert "Dos_Harina_M1" in md
    assert "AS01_Dosificado, OS01_Servidor" in md
    assert "| 4700 | Mensaje 0 | Alarm |" in md


def test_avisa_si_el_formato_no_se_puede_abrir(tmp_path):
    ruta = tmp_path / "proyecto.7z"
    ruta.write_bytes(b"7z\xbc\xaf\x27\x1c")
    with pytest.raises(ValueError, match="no es ni una carpeta ni un zip"):
        radiografiar(ruta)
