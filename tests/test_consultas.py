"""Pruebas de las consultas que se usan durante la guardia."""

import pytest

from guardias import consultas
from guardias.db import abrir, insertar


@pytest.fixture()
def con():
    conexion = abrir(":memory:")
    yield conexion
    conexion.close()


@pytest.fixture()
def planta(con):
    return insertar(con, "planta", {"codigo": "ANT", "nombre": "Antequera"})


def test_consulta_fts_limpia_los_signos():
    # El texto se dicta por teléfono y llega con comillas y guiones que FTS5
    # interpretaría como sintaxis.
    assert consultas.consulta_fts('fallo - "báscula" 2') == '"fallo" "báscula" "2"*'
    assert consultas.consulta_fts("   ") == ""
    assert consultas.consulta_fts("-*-") == ""


def test_buscar_no_revienta_con_sintaxis_fts(con, planta):
    insertar(con, "alarma", {"planta_id": planta, "texto": "Fallo báscula 2"})
    assert consultas.buscar(con, 'NOT "" OR (') == []


def test_buscar_encuentra_alarma_por_texto_parcial(con, planta):
    insertar(
        con,
        "alarma",
        {"planta_id": planta, "codigo": "4711", "texto": "Sobrecarga dosificador harina 1",
         "causa": "Tolva atascada"},
    )
    (resultado,) = consultas.buscar(con, "dosificador")
    assert resultado["entidad"] == "alarma"

    # Busca también por la causa, no solo por el texto de la alarma.
    assert consultas.buscar(con, "tolva")


def test_buscar_ignora_acentos(con, planta):
    insertar(con, "alarma", {"planta_id": planta, "texto": "Fallo válvula agua"})
    assert consultas.buscar(con, "valvula")


def test_indice_se_actualiza_al_editar_y_borrar(con, planta):
    id_ = insertar(con, "alarma", {"planta_id": planta, "texto": "Fallo amasadora"})
    con.execute("UPDATE alarma SET texto = 'Fallo divisora' WHERE id = ?", (id_,))
    con.commit()
    assert consultas.buscar(con, "amasadora") == []
    assert consultas.buscar(con, "divisora")

    con.execute("DELETE FROM alarma WHERE id = ?", (id_,))
    con.commit()
    assert consultas.buscar(con, "divisora") == []


def test_reincidencias_se_limitan_a_la_misma_planta(con, planta):
    otra = insertar(con, "planta", {"codigo": "VLC", "nombre": "Valencia"})
    insertar(con, "incidencia", {"planta_id": planta, "titulo": "Sobrecarga dosificador harina"})
    insertar(con, "incidencia", {"planta_id": otra, "titulo": "Sobrecarga dosificador harina"})
    actual = insertar(con, "incidencia", {"planta_id": planta, "titulo": "Sobrecarga dosificador harina"})

    fila = con.execute("SELECT * FROM incidencia WHERE id = ?", (actual,)).fetchone()
    parecidas = consultas.reincidencias(con, fila)

    assert [p["entidad_id"] for p in parecidas] == [1]  # ni ella misma ni la de Valencia


def test_guardia_activa_segun_la_hora(con):
    insertar(
        con,
        "guardia",
        {"tecnico": "Borja", "inicio": "2000-01-01 00:00:00", "fin": "2000-01-02 00:00:00"},
    )
    assert consultas.guardia_activa(con) is None

    insertar(
        con,
        "guardia",
        {"tecnico": "Borja", "inicio": "2000-01-01 00:00:00", "fin": "2999-01-01 00:00:00"},
    )
    assert consultas.guardia_activa(con)["tecnico"] == "Borja"


def test_resumen_y_actividad(con, planta):
    insertar(con, "incidencia", {"planta_id": planta, "titulo": "Aviso", "parada_min": 45})
    insertar(con, "incidencia", {"planta_id": planta, "titulo": "Otro", "estado": "cerrada"})

    resumen = consultas.resumen(con)
    assert resumen["plantas"] == 1
    assert resumen["abiertas"] == 1
    assert resumen["ultimos_30d"] == 2
    assert resumen["parada_30d"] == 45

    (fila,) = consultas.actividad_por_planta(con)
    assert fila["avisos"] == 2 and fila["parada"] == 45


def test_buscar_simbolos_por_direccion_y_comentario(con, planta):
    proyecto = insertar(con, "proyecto", {"planta_id": planta, "nombre": "Dosificado"})
    insertar(
        con,
        "simbolo",
        {"proyecto_id": proyecto, "nombre": "Peso_Harina", "direccion": "DB12.DBD4",
         "comentario": "Peso báscula tolva"},
    )
    assert consultas.buscar_simbolos(con, "DB12")
    assert consultas.buscar_simbolos(con, "tolva")
    assert consultas.buscar_simbolos(con, "no_existe") == []


def test_busqueda_flexible_encuentra_aunque_falte_una_palabra(con, planta):
    # El texto pegado del SCADA no coincide palabra por palabra con el título
    # que se escribió en el aviso de hace meses.
    insertar(con, "incidencia", {"planta_id": planta, "titulo": "Sobrecarga dosificador harina 1"})
    consulta = "Dosificador harina 1: sobrecarga motor"

    assert consultas.buscar(con, consulta, entidad="incidencia") == []
    assert consultas.buscar(con, consulta, entidad="incidencia", flexible=True)


def test_la_busqueda_flexible_ordena_por_coincidencias(con, planta):
    insertar(con, "incidencia", {"planta_id": planta, "titulo": "Sobrecarga dosificador harina 1"})
    insertar(con, "incidencia", {"planta_id": planta, "titulo": "Fallo del motor de la divisora"})

    filas = consultas.buscar(con, "sobrecarga dosificador harina motor",
                             entidad="incidencia", flexible=True)
    assert filas[0]["titulo"] == "Sobrecarga dosificador harina 1"


def test_la_busqueda_estricta_sigue_exigiendo_todas_las_palabras(con, planta):
    insertar(con, "alarma", {"planta_id": planta, "texto": "Fallo báscula 2"})
    assert consultas.buscar(con, "fallo bascula") 
    assert consultas.buscar(con, "fallo bascula amasadora") == []


def test_consulta_fts_flexible():
    assert consultas.consulta_fts("fallo bascula") == '"fallo" "bascula"*'
    assert consultas.consulta_fts("fallo bascula", flexible=True) == '"fallo" OR "bascula"*'
    assert consultas.consulta_fts("", flexible=True) == ""
