"""Pruebas de la lectura de la carpeta de un multiproyecto STEP7 / PCS7."""

import pytest

from guardias.db import abrir, insertar
from guardias.importadores.estacion import (
    importar_estacion,
    leer_multiproyecto,
    parsear_referencias,
    parsear_versiones,
    solo_relevantes,
)


def ver(*cadenas: str) -> bytes:
    """Reconstruye el formato del .ver: cada cadena tras un byte de longitud."""
    salida = bytearray(b"_\x00")
    for c in cadenas:
        bruto = c.encode("cp1252")
        salida += bytes([len(bruto)]) + bruto
    return bytes(salida)


ENVREF = """<?xml version="1.0" standalone="yes"?>
<envs version="1.0" last_id="12">
<env id="11" guid="{D6628D8C}" obj_type="1122305" host_name="RIB-EST-ING-V9"
     local_path="C:\\Program Files (x86)\\SIEMENS\\STEP7\\S7Proj\\C700_N_7\\C700_AS\\C700_AS.s7p"
     env_name="C700_AS"/>
<env id="12" guid="{E949CE6F}" obj_type="1122305" host_name="RIB-EST-ING-V9"
     local_path="C:\\Program Files (x86)\\SIEMENS\\STEP7\\S7Proj\\C700_N_7\\C700_OS\\C700_OS.s7p"
     env_name="C700_OS"/>
</envs>"""


def test_lee_producto_y_version():
    datos = ver("STEP 7", "V5.6 + HF3", "5.6", "K5.6.0.3")
    assert parsear_versiones(datos) == [{"producto": "STEP 7", "version": "V5.6 + HF3"}]


def test_una_version_con_upd_no_se_toma_por_nombre():
    # "Upd" son tres letras seguidas: clasificando por letras, esta versión
    # pasaría por producto y dejaría al suyo sin versión.
    datos = ver("WinCC Advanced Process Control", "V7.4 + SP1 + Upd4", "7.4")
    (producto,) = parsear_versiones(datos)
    assert producto == {
        "producto": "WinCC Advanced Process Control",
        "version": "V7.4 + SP1 + Upd4",
    }


@pytest.mark.parametrize(
    "version",
    ["V5.6 + HF3", "V9.0+SP1", "K5.6.0.3_7.1.0.1", "3.9", "2014 SP3",
     "V09.00.01.00_00.00.00.58", "V5.4 + SP5 + Upd2", "V14.0 SP1 + Upd2"],
)
def test_formatos_de_version_reales(version):
    (producto,) = parsear_versiones(ver("Producto X", version))
    assert producto["version"] == version


def test_un_nombre_que_lleva_version_dentro_sigue_siendo_nombre():
    datos = ver("DSP STARTER V5.1.1.0", "5.1.1.0")
    (producto,) = parsear_versiones(datos)
    assert producto["producto"] == "DSP STARTER V5.1.1.0"


def test_los_nombres_no_se_pegan_a_la_version_anterior():
    # Leyendo por patrón en vez de por longitud, el byte de longitud de una
    # cadena se cuela al final de la anterior y los nombres salen pegados.
    datos = ver("SIMATIC PCS 7 Basis Library", "V9.0 + SP1",
                "SIMATIC PCS 7 Tools", "V9.0 + SP1")
    assert [p["producto"] for p in parsear_versiones(datos)] == [
        "SIMATIC PCS 7 Basis Library",
        "SIMATIC PCS 7 Tools",
    ]


def test_solo_relevantes_filtra_los_componentes_internos():
    productos = [
        {"producto": "SIMATIC PCS 7 Basis Library", "version": "V9.0 + SP1"},
        {"producto": "SIMATIC Grid Control", "version": "2.6.0.0"},
        {"producto": "STEP 7", "version": "V5.6 + HF3"},
    ]
    assert [p["producto"] for p in solo_relevantes(productos)] == [
        "SIMATIC PCS 7 Basis Library",
        "STEP 7",
    ]


def test_referencias_del_multiproyecto():
    proyectos = parsear_referencias(ENVREF)
    assert [p["nombre"] for p in proyectos] == ["C700_AS", "C700_OS"]
    assert all(p["estacion"] == "RIB-EST-ING-V9" for p in proyectos)
    assert proyectos[0]["ruta"].endswith("C700_AS\\C700_AS.s7p")


@pytest.fixture()
def multiproyecto(tmp_path):
    raiz = tmp_path / "C700_N"
    (raiz / "ApiLog").mkdir(parents=True)
    (raiz / "s7extref").mkdir()
    (raiz / "ApiLog" / "Step7Bas.ver").write_bytes(
        ver("STEP 7", "V5.6 + HF3", "SIMATIC PCS 7 Tools", "V9.0 + SP1",
            "SIMATIC Grid Control", "2.6.0.0")
    )
    (raiz / "s7extref" / "s7envref.xml").write_text(ENVREF, encoding="utf-8")
    return raiz


def test_leer_multiproyecto_detecta_que_viene_vacio(multiproyecto):
    r = leer_multiproyecto(multiproyecto)
    assert r["nombre"] == "C700_N"
    assert r["estacion_ingenieria"] == "RIB-EST-ING-V9"
    assert [p["nombre"] for p in r["proyectos"]] == ["C700_AS", "C700_OS"]
    assert r["vacio"] is True          # no hay ningún .s7p dentro de la carpeta


def test_un_multiproyecto_con_contenido_no_se_marca_vacio(multiproyecto):
    (multiproyecto / "C700_AS").mkdir()
    (multiproyecto / "C700_AS" / "C700_AS.s7p").write_bytes(b"")
    assert leer_multiproyecto(multiproyecto)["vacio"] is False


def test_importar_estacion_rellena_el_software_de_la_planta(multiproyecto):
    con = abrir(":memory:")
    planta = insertar(con, "planta", {"codigo": "C700", "nombre": "Ribarroja"})

    r = importar_estacion(con, planta, multiproyecto)
    assert r["nuevos"] == 2            # Grid Control se queda fuera por defecto

    filas = con.execute(
        "SELECT producto, version, notas FROM software WHERE planta_id = ?"
        " ORDER BY producto", (planta,)
    ).fetchall()
    assert [f["producto"] for f in filas] == ["SIMATIC PCS 7 Tools", "STEP 7"]
    assert "RIB-EST-ING-V9" in filas[0]["notas"]

    # Reimportar no duplica.
    assert importar_estacion(con, planta, multiproyecto)["nuevos"] == 0
    assert con.execute("SELECT count(*) FROM software").fetchone()[0] == 2


def test_dos_versiones_de_la_misma_libreria_se_guardan_las_dos(tmp_path):
    # Una estación puede arrastrar la librería vieja junto a la nueva.
    from tests.test_estacion import ver as _ver

    raiz = tmp_path / "C700_N"
    (raiz / "ApiLog").mkdir(parents=True)
    (raiz / "ApiLog" / "Step7Bas.ver").write_bytes(
        _ver("SIMATIC PCS 7 Basis Library", "V7.1 + SP3 + Upd11",
             "SIMATIC PCS 7 Basis Library", "V9.0 + SP1")
    )
    con = abrir(":memory:")
    planta = insertar(con, "planta", {"codigo": "C700", "nombre": "Ribarroja"})

    assert importar_estacion(con, planta, raiz)["nuevos"] == 2
    versiones = [
        f["version"] for f in con.execute(
            "SELECT version FROM software ORDER BY version")
    ]
    assert versiones == ["V7.1 + SP3 + Upd11", "V9.0 + SP1"]
    assert importar_estacion(con, planta, raiz)["nuevos"] == 0


def test_importar_estacion_con_todo_guarda_los_componentes_internos(multiproyecto):
    con = abrir(":memory:")
    planta = insertar(con, "planta", {"codigo": "C700", "nombre": "Ribarroja"})
    assert importar_estacion(con, planta, multiproyecto, todo=True)["nuevos"] == 3
