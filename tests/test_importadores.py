"""Pruebas de los importadores de exportaciones de Siemens."""

import textwrap

import pytest

from guardias.db import abrir, insertar
from guardias.importadores import (
    importar_alarmas,
    importar_proyecto,
    leer_metadatos_archivo,
    parsear_alarmas,
    importar_simbolos,
    parsear_simbolos,
)
from guardias.importadores.texto import decodificar, detectar_delimitador


@pytest.fixture()
def con():
    conexion = abrir(":memory:")
    yield conexion
    conexion.close()


def linea_asc(nombre, direccion, tipo, comentario):
    return "126," + nombre.ljust(24) + direccion.ljust(12) + tipo.ljust(10) + comentario.ljust(80)


# ------------------------------------------------------------------ símbolos


def test_simbolos_asc_ancho_fijo():
    texto = "\n".join(
        [
            linea_asc("Dos_Harina_M1", "E      0.0", "BOOL", "Marcha motor tolva 1"),
            linea_asc("Bascula_Peso", "DB12.DBD 4", "REAL", "Peso báscula harina"),
        ]
    )
    simbolos = parsear_simbolos(texto)
    assert [s["nombre"] for s in simbolos] == ["Dos_Harina_M1", "Bascula_Peso"]
    # El relleno de ancho fijo deja espacios dentro del operando.
    assert simbolos[0]["direccion"] == "E 0.0"
    assert simbolos[1]["tipo_dato"] == "REAL"
    assert simbolos[1]["comentario"] == "Peso báscula harina"


def test_simbolos_sdf_entrecomillado():
    texto = '"Dos_Agua_V1","A      4.2","BOOL","Válvula agua"\n'
    (simbolo,) = parsear_simbolos(texto)
    assert simbolo["nombre"] == "Dos_Agua_V1"
    assert simbolo["direccion"] == "A 4.2"


def test_simbolos_csv_con_cabecera_en_ingles():
    texto = textwrap.dedent(
        """\
        Symbol;Address;Data type;Comment
        Amasadora_M1;E 1.0;BOOL;Marcha amasadora
        """
    )
    (simbolo,) = parsear_simbolos(texto)
    assert simbolo["nombre"] == "Amasadora_M1"
    assert simbolo["comentario"] == "Marcha amasadora"


def test_simbolos_columnas_desordenadas_por_cabecera():
    texto = "Comentario\tDireccion\tSimbolo\tTipo\nPeso masa\tDB5.DBD0\tPeso_Masa\tREAL\n"
    (simbolo,) = parsear_simbolos(texto)
    assert simbolo["nombre"] == "Peso_Masa"
    assert simbolo["direccion"] == "DB5.DBD0"
    assert simbolo["comentario"] == "Peso masa"


def test_simbolos_importa_y_reemplaza(con):
    planta = insertar(con, "planta", {"codigo": "T1", "nombre": "Prueba"})
    proyecto = insertar(con, "proyecto", {"planta_id": planta, "nombre": "P"})

    importar_simbolos(con, proyecto, "A;E 0.0;BOOL;uno\nB;E 0.1;BOOL;dos\n")
    assert con.execute("SELECT count(*) FROM simbolo").fetchone()[0] == 2

    # Una versión nueva del programa sustituye la tabla entera.
    importar_simbolos(con, proyecto, "C;E 0.2;BOOL;tres\n")
    nombres = [f[0] for f in con.execute("SELECT nombre FROM simbolo")]
    assert nombres == ["C"]


# ------------------------------------------------------------------- alarmas


def test_alarmas_cabecera_alemana():
    texto = "Nummer;Meldetext;Klasse;Priorität\n4711;Dosificador harina sobrecarga;Alarm;1\n"
    (alarma,) = parsear_alarmas(texto)
    assert alarma["codigo"] == "4711"
    assert alarma["texto"] == "Dosificador harina sobrecarga"
    assert alarma["criticidad"] == "alta"


def test_alarmas_sin_cabecera_usa_las_dos_primeras_columnas():
    (alarma,) = parsear_alarmas("9001\tFallo báscula 2\n")
    assert alarma["codigo"] == "9001"
    assert alarma["texto"] == "Fallo báscula 2"


def test_alarmas_reimportar_conserva_el_conocimiento(con):
    planta = insertar(con, "planta", {"codigo": "T1", "nombre": "Prueba"})
    importar_alarmas(con, "Number;Message text\n4711;Sobrecarga\n", planta_id=planta)

    con.execute(
        "UPDATE alarma SET causa = ?, actuacion = ? WHERE codigo = '4711'",
        ("Tolva atascada", "Vaciar tolva y rearmar"),
    )
    con.commit()

    # Nueva exportación del SCADA con el texto corregido.
    resultado = importar_alarmas(
        con, "Number;Message text\n4711;Sobrecarga dosificador harina 1\n", planta_id=planta
    )
    fila = con.execute("SELECT * FROM alarma WHERE codigo = '4711'").fetchone()
    assert resultado == {"nuevas": 0, "actualizadas": 1, "leidas": 1}
    assert fila["texto"] == "Sobrecarga dosificador harina 1"
    assert fila["causa"] == "Tolva atascada"          # lo escrito a mano no se pisa
    assert fila["actuacion"] == "Vaciar tolva y rearmar"


def test_alarmas_misma_codificacion_distintas_plantas(con):
    a = insertar(con, "planta", {"codigo": "A", "nombre": "A"})
    b = insertar(con, "planta", {"codigo": "B", "nombre": "B"})
    importar_alarmas(con, "Number;Message text\n10;Fallo\n", planta_id=a)
    importar_alarmas(con, "Number;Message text\n10;Fallo\n", planta_id=b)
    assert con.execute("SELECT count(*) FROM alarma").fetchone()[0] == 2


def test_decodifica_cp1252_de_una_estacion_de_ingenieria():
    assert "válvula" in decodificar("válvula".encode("cp1252"))


def test_detecta_delimitador_estable():
    assert detectar_delimitador("a;b;c\nd;e;f") == ";"
    assert detectar_delimitador("a\tb\tc\nd\te\tf") == "\t"


# ----------------------------------------------------------------- proyectos


def _zap_de_prueba(tmp_path):
    import zipfile

    ruta = tmp_path / "Dosificado_Antequera.zap17"
    with zipfile.ZipFile(ruta, "w") as z:
        z.writestr("AS01/programa.txt", "bloques")
        z.writestr("OS01/pantallas.txt", "pdl")
    return ruta


def test_metadatos_deducen_version_y_estaciones(tmp_path):
    meta = leer_metadatos_archivo(_zap_de_prueba(tmp_path))
    assert meta["version_pcs7"] == "TIA Portal V17"
    assert meta["estaciones"] == ["AS01", "OS01"]
    assert len(meta["sha256"]) == 64
    assert len(meta["entradas"]) == 2


def test_importar_proyecto_no_duplica_la_misma_copia(con, tmp_path):
    planta = insertar(con, "planta", {"codigo": "T1", "nombre": "Prueba"})
    ruta = _zap_de_prueba(tmp_path)

    primero = importar_proyecto(con, planta, ruta, origen="Siemens")
    segundo = importar_proyecto(con, planta, ruta)

    assert primero["duplicado"] is False
    assert segundo["duplicado"] is True
    assert segundo["proyecto_id"] == primero["proyecto_id"]
    assert con.execute("SELECT count(*) FROM proyecto_entrada").fetchone()[0] == 2


def test_importar_proyecto_acepta_archivo_no_zip(con, tmp_path):
    planta = insertar(con, "planta", {"codigo": "T1", "nombre": "Prueba"})
    ruta = tmp_path / "copia.zip"
    ruta.write_bytes(b"no soy un zip")
    resultado = importar_proyecto(con, planta, ruta)
    assert resultado["entradas"] == []
    assert resultado["proyecto_id"] > 0
