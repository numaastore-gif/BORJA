"""Pruebas de la localización y extracción de archivados de proyecto."""

import zipfile
from datetime import date

import pytest

from guardias.archivar import candidatos, extraer, fecha_de_nombre, tablas_de_simbolos


def zap(directorio, nombre, entradas=(("AS01/programa.txt", "bloques"),)):
    ruta = directorio / nombre
    with zipfile.ZipFile(ruta, "w") as z:
        for interno, contenido in entradas:
            z.writestr(interno, contenido)
    return ruta


@pytest.mark.parametrize(
    "nombre, esperada",
    [
        ("Dosificado_C700_20260918.zap17", date(2026, 9, 18)),
        ("C700 21-09-2026.zip", date(2026, 9, 21)),
        ("PLC_C700_210926.zap", date(2026, 9, 21)),
        ("Copia 2026-09-21 final.zip", date(2026, 9, 21)),
        ("Dosificado_C700.zip", None),
        ("C700_20261332.zip", None),          # fecha imposible: se ignora
    ],
)
def test_fecha_de_nombre(nombre, esperada):
    assert fecha_de_nombre(nombre) == esperada


def test_la_fecha_del_nombre_manda_sobre_el_mtime(tmp_path):
    # Al copiar entre unidades de red el mtime deja de ser fiable, así que el
    # archivado más nuevo por nombre debe ganar aunque se haya copiado antes.
    antiguo = zap(tmp_path, "C700_20260101.zap17")
    nuevo = zap(tmp_path, "C700_20260918.zap17")
    import os

    os.utime(nuevo, (0, 0))          # el nuevo aparenta ser el más viejo
    os.utime(antiguo, None)

    orden = [c["nombre"] for c in candidatos(tmp_path)]
    assert orden[0] == "C700_20260918.zap17"


def test_sin_fecha_en_el_nombre_se_usa_el_mtime(tmp_path):
    import os

    viejo = zap(tmp_path, "copia_vieja.zip")
    reciente = zap(tmp_path, "copia_nueva.zip")
    os.utime(viejo, (0, 0))

    resultado = candidatos(tmp_path)
    assert resultado[0]["nombre"] == "copia_nueva.zip"
    assert resultado[0]["fecha_nombre"] is None


def test_candidatos_ignora_lo_que_no_es_archivado(tmp_path):
    zap(tmp_path, "C700.zap17")
    (tmp_path / "notas.txt").write_text("nada")
    (tmp_path / "subcarpeta").mkdir()
    assert [c["nombre"] for c in candidatos(tmp_path)] == ["C700.zap17"]


def test_directorio_inaccesible(tmp_path):
    with pytest.raises(NotADirectoryError):
        candidatos(tmp_path / "no_existe")


def test_extraer_crea_la_carpeta_con_el_contenido(tmp_path):
    ruta = zap(tmp_path, "C700_20260918.zap17", [("AS01/prog.txt", "x"), ("OS01/pdl.txt", "y")])
    carpeta = extraer(ruta, tmp_path / "salida")
    assert carpeta.name == "C700_20260918"
    assert (carpeta / "AS01" / "prog.txt").read_text() == "x"
    assert (carpeta / "OS01" / "pdl.txt").read_text() == "y"


def test_extraer_rechaza_rutas_que_se_salen_del_destino(tmp_path):
    # Los archivados vienen del cliente: no se da por buena su ruta interna.
    ruta = tmp_path / "malicioso.zip"
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("../fuera.txt", "no debería escribirse")

    with pytest.raises(ValueError, match="fuera del destino"):
        extraer(ruta, tmp_path / "salida")
    assert not (tmp_path / "fuera.txt").exists()


def test_extraer_avisa_si_no_es_un_zip(tmp_path):
    ruta = tmp_path / "C700.7z"
    ruta.write_bytes(b"7z\xbc\xaf\x27\x1c")
    with pytest.raises(ValueError, match="no es un zip"):
        extraer(ruta, tmp_path / "salida")


def test_encuentra_las_tablas_de_simbolos_extraidas(tmp_path):
    ruta = zap(
        tmp_path,
        "C700.zap17",
        [("AS01/simbolos.asc", "126,x"), ("AS01/prog.txt", "x"), ("OS01/lista.SDF", '"a"')],
    )
    carpeta = extraer(ruta, tmp_path / "salida")
    assert [t.name for t in tablas_de_simbolos(carpeta)] == ["simbolos.asc", "lista.SDF"]
