"""Carga unos datos de ejemplo para ver la herramienta funcionando.

    python -m guardias.ejemplo            # sobre la base por defecto
    GUARDIAS_BD=/tmp/demo.db python -m guardias.ejemplo

Los datos son inventados: sirven para entender la estructura antes de meter
los de las plantas de verdad.
"""

from __future__ import annotations

import sqlite3

from .db import abrir, insertar
from .importadores import importar_alarmas

ALARMAS_DEMO = """Number;Message text;Klasse;Priority
4711;Dosificador harina 1: sobrecarga motor;Alarm;1
4712;Bascula harina 1: fuera de tolerancia;Alarm;2
4713;Tolva harina 1: nivel minimo;Warning;3
4801;Amasadora 1: fallo variador;Alarm;1
4802;Agua de proceso: temperatura fuera de rango;Warning;2
"""


def sembrar(con: sqlite3.Connection) -> None:
    planta = insertar(
        con,
        "planta",
        {
            "codigo": "ANT-01",
            "nombre": "Bloque de pan — línea de dosificado",
            "localidad": "Antequera",
            "provincia": "Málaga",
            "tipo_linea": "Pan de molde y bollería",
            "criticidad": "alta",
            "horario": "Producción 24/5, parada técnica domingos",
            "acceso_remoto": "VPN del cliente + salto a la ES. Credenciales en el gestor del equipo.",
        },
    )

    insertar(con, "contacto", {
        "planta_id": planta, "nombre": "Jefe de turno", "rol": "Producción",
        "telefono": "600 00 00 00", "prioridad": 1, "horario": "24/5",
    })
    insertar(con, "contacto", {
        "planta_id": planta, "nombre": "Mantenimiento eléctrico", "rol": "Mantenimiento",
        "telefono": "600 00 00 01", "prioridad": 2,
    })

    for equipo in (
        {"tipo": "AS", "nombre": "AS01 dosificado", "modelo": "CPU 410-5H",
         "referencia": "6ES7410-5HX08-0AB0", "ip": "10.20.1.10", "red": "Bus de planta"},
        {"tipo": "OS", "nombre": "OS servidor", "modelo": "IPC647E", "ip": "10.20.1.20",
         "red": "Bus de terminales"},
        {"tipo": "ET200", "nombre": "ET200M tolvas", "modelo": "IM153-2",
         "red": "Profibus DP1", "ubicacion": "Armario A2", "repuesto": 1},
        {"tipo": "bascula", "nombre": "Báscula harina 1", "fabricante": "Siemens",
         "modelo": "SIWAREX WP241", "red": "Profibus DP1"},
    ):
        insertar(con, "equipo", {"planta_id": planta, **equipo})

    insertar(con, "software", {
        "planta_id": planta, "producto": "SIMATIC PCS7", "version": "V9.1",
        "service_pack": "SP2", "licencia": "Dongle en la ES de planta",
    })

    importar_alarmas(con, ALARMAS_DEMO, planta_id=planta)
    con.execute(
        "UPDATE alarma SET causa = ?, actuacion = ?, verificada = 1 WHERE codigo = '4711'",
        (
            "Atasco de harina en la tolva o rodamiento del sinfín agarrotado.",
            "1. Parar el dosificador desde el SCADA.\n"
            "2. Comprobar nivel y apelmazado en la tolva.\n"
            "3. Rearmar el variador y verificar consumo en vacío.\n"
            "4. Si el consumo sigue alto, avisar a mantenimiento mecánico.",
        ),
    )
    con.commit()

    guardia = insertar(con, "guardia", {
        "tecnico": "Borja", "inicio": "2026-09-21 08:00:00", "fin": "2026-09-28 08:00:00",
        "telefono": "600 00 00 02",
    })

    alarma = con.execute("SELECT id FROM alarma WHERE codigo = '4711'").fetchone()["id"]
    insertar(con, "incidencia", {
        "planta_id": planta, "guardia_id": guardia, "alarma_id": alarma,
        "titulo": "Sobrecarga dosificador harina 1",
        "recibido": "2026-09-21 03:12:00", "cerrado": "2026-09-21 03:47:00",
        "canal": "teléfono", "avisado_por": "Jefe de turno", "area": "Dosificado harinas",
        "sintoma": "El SCADA da sobrecarga del motor y la línea queda parada.",
        "diagnostico": "Harina apelmazada en la tolva por humedad.",
        "solucion": "Vaciada la tolva, rearmado el variador y verificado el consumo en vacío.",
        "parada_min": 35, "resuelto_remoto": 1, "estado": "cerrada", "criticidad": "alta",
        "acciones": "Proponer revisión del vibrador de la tolva en la próxima parada técnica.",
        "etiquetas": "dosificado, harina, variador",
    })


def main() -> None:
    con = abrir()
    if con.execute("SELECT count(*) FROM planta").fetchone()[0]:
        print("La base ya tiene plantas: no se cargan los datos de ejemplo.")
        return
    sembrar(con)
    print("Datos de ejemplo cargados. Arranca con: python -m guardias --abrir")


if __name__ == "__main__":
    main()
