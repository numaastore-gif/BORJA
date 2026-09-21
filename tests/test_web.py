"""Pruebas de extremo a extremo de la interfaz web."""

from urllib.parse import unquote

import pytest
from fastapi.testclient import TestClient

from guardias.web import crear_app


@pytest.fixture()
def cliente(tmp_path, monkeypatch):
    monkeypatch.setenv("GUARDIAS_ADJUNTOS", str(tmp_path / "adjuntos"))
    app = crear_app(tmp_path / "prueba.db")
    with TestClient(app) as c:
        yield c


def crear_planta(cliente, codigo="ANT", nombre="Antequera"):
    r = cliente.post("/plantas", data={"codigo": codigo, "nombre": nombre}, follow_redirects=False)
    assert r.status_code == 303
    return int(r.headers["location"].rsplit("/", 1)[1])


def test_panel_vacio_responde(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    assert "Panel de guardia" in r.text


def test_alta_de_planta_y_ficha(cliente):
    planta = crear_planta(cliente)
    r = cliente.get(f"/plantas/{planta}")
    assert r.status_code == 200
    assert "Antequera" in r.text

    cliente.post(
        f"/plantas/{planta}/equipos",
        data={"tipo": "AS", "nombre": "AS01 dosificado", "modelo": "CPU 410-5H", "ip": "10.1.1.10"},
    )
    cliente.post(
        f"/plantas/{planta}/contactos",
        data={"nombre": "Jefe de turno", "telefono": "600000000", "prioridad": "1"},
    )
    r = cliente.get(f"/plantas/{planta}")
    assert "CPU 410-5H" in r.text and "600000000" in r.text


def test_ciclo_completo_de_un_aviso(cliente):
    planta = crear_planta(cliente)

    r = cliente.post(
        "/incidencias",
        data={
            "planta_id": str(planta),
            "titulo": "Sobrecarga dosificador harina 1",
            "recibido": "2026-09-20T03:15",
            "sintoma": "El SCADA marca sobrecarga y la línea para",
            "criticidad": "alta",
        },
        follow_redirects=False,
    )
    assert r.status_code == 303
    incidencia = int(r.headers["location"].rsplit("/", 1)[1])

    # La fecha del navegador se guarda en el formato de SQLite.
    r = cliente.get(f"/incidencias/{incidencia}")
    assert "2026-09-20 03:15:00" in r.text

    cliente.post(
        f"/incidencias/{incidencia}",
        data={
            "planta_id": str(planta),
            "titulo": "Sobrecarga dosificador harina 1",
            "estado": "cerrada",
            "solucion": "Vaciada la tolva y rearmado el variador",
            "parada_min": "35",
            "resuelto_remoto": "1",
        },
    )
    r = cliente.get(f"/incidencias/{incidencia}")
    assert "Vaciada la tolva" in r.text
    assert "cerrada" in r.text

    # Al cerrar sin fecha explícita se sella la hora de cierre.
    fila = cliente.app.state.con.execute(
        "SELECT cerrado, resuelto_remoto FROM incidencia WHERE id = ?", (incidencia,)
    ).fetchone()
    assert fila["cerrado"] is not None
    assert fila["resuelto_remoto"] == 1


def test_casilla_no_marcada_se_guarda_como_cero(cliente):
    planta = crear_planta(cliente)
    r = cliente.post(
        "/incidencias",
        data={"planta_id": str(planta), "titulo": "Aviso", "resuelto_remoto": "1"},
        follow_redirects=False,
    )
    incidencia = int(r.headers["location"].rsplit("/", 1)[1])

    # El navegador no envía la casilla cuando se desmarca.
    cliente.post(
        f"/incidencias/{incidencia}",
        data={"planta_id": str(planta), "titulo": "Aviso", "estado": "abierta"},
    )
    fila = cliente.app.state.con.execute(
        "SELECT resuelto_remoto FROM incidencia WHERE id = ?", (incidencia,)
    ).fetchone()
    assert fila["resuelto_remoto"] == 0


def test_el_aviso_se_asigna_al_turno_en_curso(cliente):
    planta = crear_planta(cliente)
    cliente.post(
        "/guardias",
        data={"tecnico": "Borja", "inicio": "2000-01-01T00:00", "fin": "2999-01-01T00:00"},
    )
    r = cliente.post(
        "/incidencias",
        data={"planta_id": str(planta), "titulo": "Aviso nocturno"},
        follow_redirects=False,
    )
    incidencia = int(r.headers["location"].rsplit("/", 1)[1])
    fila = cliente.app.state.con.execute(
        "SELECT guardia_id FROM incidencia WHERE id = ?", (incidencia,)
    ).fetchone()
    assert fila["guardia_id"] == 1

    assert "Borja" in cliente.get("/").text


def test_importar_alarmas_por_la_web_y_buscarlas(cliente):
    planta = crear_planta(cliente)
    fichero = b"Number;Message text;Klasse\n4711;Sobrecarga dosificador harina 1;Alarm\n"

    r = cliente.post(
        "/importar/alarmas",
        data={"planta_id": str(planta)},
        files={"fichero": ("mensajes.csv", fichero, "text/csv")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "1 nuevas" in unquote(r.headers["location"])

    assert "Sobrecarga" in cliente.get("/alarmas?q=dosificador").text
    assert "Sobrecarga" in cliente.get("/buscar?q=sobrecarga").text


def test_busqueda_con_comillas_no_da_error(cliente):
    assert cliente.get('/buscar?q=fallo - "báscula"').status_code == 200


def test_abrir_aviso_desde_una_alarma(cliente):
    planta = crear_planta(cliente)
    r = cliente.post(
        "/alarmas",
        data={
            "planta_id": str(planta), "codigo": "4711", "texto": "Fallo báscula 2",
            "criticidad": "alta", "actuacion": "Tarar la báscula",
        },
        follow_redirects=False,
    )
    alarma = int(r.headers["location"].rsplit("/", 1)[1])

    r = cliente.get(f"/incidencias/nueva?alarma_id={alarma}")
    assert "Fallo báscula 2" in r.text  # el título viene relleno

    r = cliente.post(
        "/incidencias",
        data={"planta_id": str(planta), "titulo": "Fallo báscula 2", "alarma_id": str(alarma)},
        follow_redirects=False,
    )
    incidencia = int(r.headers["location"].rsplit("/", 1)[1])
    # La alarma muestra el histórico de veces que ha saltado.
    assert f"/incidencias/{incidencia}" in cliente.get(f"/alarmas/{alarma}").text


def test_subir_proyecto_y_su_tabla_de_simbolos(cliente, tmp_path):
    import io
    import zipfile

    planta = crear_planta(cliente)
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w") as z:
        z.writestr("AS01/programa.txt", "bloques")

    r = cliente.post(
        "/importar/proyecto",
        data={"planta_id": str(planta), "nombre": "Dosificado", "origen": "Siemens"},
        files={"fichero": ("Dosificado.zap17", memoria.getvalue(), "application/zip")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    proyecto = int(r.headers["location"].rsplit("/", 1)[1])

    r = cliente.get(f"/proyectos/{proyecto}")
    assert "TIA Portal V17" in r.text and "AS01/programa.txt" in r.text

    cliente.post(
        "/importar/simbolos",
        data={"proyecto_id": str(proyecto)},
        files={"fichero": ("simbolos.csv", b"Peso_Harina;DB12.DBD4;REAL;Peso tolva\n", "text/csv")},
    )
    assert "Peso_Harina" in cliente.get(f"/proyectos/{proyecto}?q=DB12").text
    assert "Peso_Harina" in cliente.get("/buscar?q=tolva").text


def test_borrar_solo_afecta_a_tablas_permitidas(cliente):
    planta = crear_planta(cliente)
    r = cliente.post("/borrar/busqueda/1", data={"destino": "/plantas"}, follow_redirects=False)
    assert r.status_code == 303  # se ignora en silencio, sin tocar nada

    cliente.post(f"/borrar/planta/{planta}", data={"destino": "/plantas"})
    assert cliente.app.state.con.execute("SELECT count(*) FROM planta").fetchone()[0] == 0


def test_paginas_inexistentes_redirigen_al_listado(cliente):
    for url, destino in [
        ("/plantas/999", "/plantas"),
        ("/incidencias/999", "/incidencias"),
        ("/alarmas/999", "/alarmas"),
        ("/proyectos/999", "/plantas"),
    ]:
        r = cliente.get(url, follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"] == destino


def test_api_de_busqueda_devuelve_json(cliente):
    planta = crear_planta(cliente)
    cliente.post("/alarmas", data={"planta_id": str(planta), "texto": "Fallo amasadora"})
    datos = cliente.get("/api/buscar?q=amasadora").json()
    assert datos and datos[0]["entidad"] == "alarma"


def test_el_extracto_de_busqueda_escapa_el_html(cliente):
    planta = crear_planta(cliente)
    cliente.post(
        "/alarmas",
        data={"planta_id": str(planta), "texto": "Fallo amasadora",
              "causa": "<script>alert(1)</script> correa suelta"},
    )
    r = cliente.get("/buscar?q=correa")
    assert "<script>" not in r.text
    assert "&lt;script&gt;" in r.text
    assert "<mark>correa</mark>" in r.text   # el resaltado sí se aplica


def test_subir_la_carpeta_del_multiproyecto(cliente):
    import io
    import zipfile

    from tests.test_estacion import ENVREF, ver

    planta = crear_planta(cliente, "C700", "Ribarroja")
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w") as z:
        z.writestr("C700_N/ApiLog/Step7Bas.ver",
                   ver("STEP 7", "V5.6 + HF3", "WinCC Runtime", "V7.4 + SP1 + Upd4"))
        z.writestr("C700_N/s7extref/s7envref.xml", ENVREF)

    r = cliente.post(
        "/importar/estacion",
        data={"planta_id": str(planta)},
        files={"fichero": ("C700_N.zip", memoria.getvalue(), "application/zip")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    destino = unquote(r.headers["location"])
    assert "2 productos nuevos" in destino
    assert "RIB-EST-ING-V9" in destino
    assert "C700_AS, C700_OS" in destino
    # Avisa de que el multiproyecto no trae el programa dentro.
    assert "sin el programa" in destino

    pagina = cliente.get(f"/plantas/{planta}").text
    assert "V5.6 + HF3" in pagina and "V7.4 + SP1 + Upd4" in pagina


def test_multiproyecto_que_no_es_zip_no_rompe(cliente):
    planta = crear_planta(cliente)
    r = cliente.post(
        "/importar/estacion",
        data={"planta_id": str(planta)},
        files={"fichero": ("proyecto.7z", b"7z\xbc\xaf\x27\x1c", "application/x-7z-compressed")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "No se ha podido abrir" in unquote(r.headers["location"])


def test_pagina_de_diagnostico(cliente):
    planta = crear_planta(cliente, "C700", "Ribarroja")
    cliente.post("/alarmas", data={
        "planta_id": str(planta), "codigo": "4711",
        "texto": "Dosificador harina 1: sobrecarga motor",
        "causa": "Tolva atascada por humedad",
        "actuacion": "Vaciar la tolva y rearmar el variador",
    })

    r = cliente.get("/diagnostico?q=sobrecarga+dosificador+harina")
    assert r.status_code == 200
    assert "Tolva atascada por humedad" in r.text          # lo que ya sabe
    assert "Sobrecarga o disparo térmico del motor" in r.text   # causas típicas
    assert "no de tu planta" in r.text                     # y lo dice claramente


def test_diagnostico_sin_texto_solo_explica(cliente):
    r = cliente.get("/diagnostico")
    assert r.status_code == 200
    assert "Escribe arriba el texto de la alarma" in r.text


def test_diagnostico_sin_coincidencias(cliente):
    r = cliente.get("/diagnostico?q=blablabla")
    assert "No tengo nada para" in r.text
