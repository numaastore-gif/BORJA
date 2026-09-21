"""Pruebas de la orientación ante una alarma."""

import pytest

from guardias.db import abrir, insertar
from guardias.diagnostico import PISTAS, buscar_pistas, diagnosticar


@pytest.fixture()
def con():
    conexion = abrir(":memory:")
    yield conexion
    conexion.close()


@pytest.mark.parametrize(
    "texto, esperada",
    [
        ("Dosificador harina 1: sobrecarga motor", "sobrecarga_motor"),
        ("Báscula harina 1 fuera de tolerancia", "bascula"),
        ("ET200 esclavo 12: fallo de comunicación", "comunicacion"),
        ("Válvula agua no confirma posición", "valvula"),
        ("Tolva harina: nivel mínimo", "nivel"),
        ("Tiempo de dosificación excedido", "tiempo_dosificacion"),
        ("Amasadora 1: fallo variador", "variador"),
        ("Agua de proceso: temperatura fuera de rango", "temperatura_agua"),
        ("Seta de emergencia pulsada", "seguridad"),
        ("No arranca el lote, unidad ocupada", "receta_batch"),
        ("Sonda presión: rotura de hilo", "senal_analogica"),
        ("CPU en STOP", "cpu"),
    ],
)
def test_reconoce_las_familias_de_fallo(texto, esperada):
    assert buscar_pistas(texto)[0]["id"] == esperada


def test_no_encaja_por_trozos_de_palabra():
    # "sobrecarga" contiene "carga" (báscula) y "báscula" contiene "as" (CPU):
    # comparando sin separadores, el diagnóstico proponía cosas sin relación.
    assert [p["id"] for p in buscar_pistas("Sobrecarga motor")] == ["sobrecarga_motor"]
    assert "cpu" not in [p["id"] for p in buscar_pistas("Báscula fuera de tolerancia")]


def test_manda_la_pista_con_mas_coincidencias():
    # Menciona báscula, peso y tolerancia: tres claves de la misma familia.
    pistas = buscar_pistas("Báscula: peso fuera de tolerancia en dosificador")
    assert pistas[0]["id"] == "bascula"


def test_texto_sin_relacion_no_inventa_pistas():
    assert buscar_pistas("blablabla") == []
    assert buscar_pistas("") == []
    assert buscar_pistas("   ") == []


def test_todas_las_pistas_estan_completas():
    for p in PISTAS:
        assert p["causas"] and p["comprobaciones"] and p["claves"]
        assert p["criticidad"] in ("alta", "media", "baja")
    assert len({p["id"] for p in PISTAS}) == len(PISTAS)


def test_diagnostico_prioriza_lo_que_ya_sabes(con):
    planta = insertar(con, "planta", {"codigo": "C700", "nombre": "Ribarroja"})
    insertar(con, "alarma", {
        "planta_id": planta, "codigo": "4711",
        "texto": "Dosificador harina 1: sobrecarga motor",
        "causa": "Tolva atascada por humedad", "actuacion": "Vaciar y rearmar",
        "verificada": 1,
    })
    insertar(con, "incidencia", {
        "planta_id": planta, "titulo": "Sobrecarga dosificador harina 1",
        "solucion": "Vaciada la tolva",
    })

    r = diagnosticar(con, "Dosificador harina 1: sobrecarga motor")

    assert r["alarmas"][0]["causa"] == "Tolva atascada por humedad"
    assert r["incidencias"][0]["titulo"] == "Sobrecarga dosificador harina 1"
    assert r["pistas"][0]["id"] == "sobrecarga_motor"


def test_diagnostico_con_la_base_vacia_sigue_orientando(con):
    r = diagnosticar(con, "fallo de comunicación con la ET200")
    assert r["alarmas"] == [] and r["incidencias"] == []
    assert r["pistas"][0]["id"] == "comunicacion"


def test_diagnostico_acota_el_historico_a_la_planta(con):
    a = insertar(con, "planta", {"codigo": "C700", "nombre": "Ribarroja"})
    b = insertar(con, "planta", {"codigo": "ANT", "nombre": "Antequera"})
    insertar(con, "incidencia", {"planta_id": a, "titulo": "Sobrecarga dosificador"})
    insertar(con, "incidencia", {"planta_id": b, "titulo": "Sobrecarga dosificador"})

    r = diagnosticar(con, "sobrecarga dosificador", planta_id=a)
    assert len(r["incidencias"]) == 1


def test_diagnostico_no_revienta_con_sintaxis_fts(con):
    assert diagnosticar(con, 'NOT "" OR (')["alarmas"] == []


def test_texto_vacio_no_consulta_nada(con):
    r = diagnosticar(con, "  ")
    assert r == {"texto": "  ", "alarmas": [], "incidencias": [], "pistas": [], "simbolos": []}
