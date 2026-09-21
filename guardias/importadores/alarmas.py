"""Importación de listas de mensajes de WinCC / PCS7 a la base de alarmas.

El objetivo no es replicar el SCADA, sino sembrar la base de conocimiento con
el texto exacto que el operario de planta te va a leer por teléfono, para que
la búsqueda lo encuentre y muestre causa y actuación.
"""

from __future__ import annotations

import sqlite3

from .texto import celda, decodificar, leer_filas, mapear_columnas, parece_cabecera

ALIAS = {
    "codigo": (
        "number", "nummer", "meldenummer", "message number", "msgnr",
        "numero", "n de mensaje", "id", "alarmnumber",
    ),
    "texto": (
        "message text", "meldetext", "texto", "texto de mensaje", "text",
        "alarmtext", "event text", "descripcion",
    ),
    "clase": ("class", "klasse", "message class", "meldeklasse", "clase", "tipo"),
    "area": ("area", "bereich", "origin", "herkunft", "origen", "zona", "unidad"),
    "causa": ("cause", "ursache", "causa", "motivo"),
    "actuacion": (
        "action", "massnahme", "remedy", "abhilfe", "actuacion",
        "solucion", "medida",
    ),
    "criticidad": ("priority", "prioritat", "prioridad", "severity", "criticidad"),
}

# Prioridad numérica de WinCC -> criticidad de la ficha.
_CRITICIDAD = {"0": "alta", "1": "alta", "2": "media", "3": "media"}


def _criticidad(valor: str | None) -> str:
    if not valor:
        return "media"
    v = valor.strip().lower()
    if v in ("alta", "media", "baja"):
        return v
    return _CRITICIDAD.get(v, "media")


def parsear_alarmas(datos: bytes | str) -> list[dict]:
    """Devuelve las alarmas de una exportación, sin tocar la base."""
    texto = decodificar(datos) if isinstance(datos, bytes) else datos
    filas = leer_filas(texto)
    if not filas:
        return []

    if parece_cabecera(filas[0], ALIAS):
        mapa = mapear_columnas(filas[0], ALIAS)
        cuerpo = filas[1:]
    else:
        # Sin cabecera reconocible: número y texto son las dos primeras columnas.
        mapa = {"codigo": 0, "texto": 1}
        cuerpo = filas

    alarmas = []
    for fila in cuerpo:
        texto_alarma = celda(fila, mapa, "texto")
        if not texto_alarma:
            continue
        alarmas.append(
            {
                "codigo": celda(fila, mapa, "codigo"),
                "texto": texto_alarma,
                "clase": celda(fila, mapa, "clase"),
                "area": celda(fila, mapa, "area"),
                "causa": celda(fila, mapa, "causa"),
                "actuacion": celda(fila, mapa, "actuacion"),
                "criticidad": _criticidad(celda(fila, mapa, "criticidad")),
            }
        )
    return alarmas


def importar_alarmas(
    con: sqlite3.Connection, datos: bytes | str, *, planta_id: int | None = None
) -> dict:
    """Carga o refresca alarmas de una planta.

    Si el código ya existe para esa planta se refrescan los campos que vienen
    del SCADA (texto, clase, área) pero **nunca** se pisan la causa ni la
    actuación: ese es el conocimiento que aportas tú y no viene en el fichero.
    """
    alarmas = parsear_alarmas(datos)
    nuevas = actualizadas = 0

    for a in alarmas:
        existente = None
        if a["codigo"]:
            existente = con.execute(
                "SELECT id, causa, actuacion FROM alarma"
                " WHERE codigo = ? AND planta_id IS ?",
                (a["codigo"], planta_id),
            ).fetchone()

        if existente:
            con.execute(
                "UPDATE alarma SET texto = ?, clase = coalesce(?, clase),"
                " area = coalesce(?, area), causa = coalesce(causa, ?),"
                " actuacion = coalesce(actuacion, ?),"
                " actualizado = datetime('now') WHERE id = ?",
                (
                    a["texto"], a["clase"], a["area"],
                    a["causa"], a["actuacion"], existente["id"],
                ),
            )
            actualizadas += 1
        else:
            con.execute(
                "INSERT INTO alarma (planta_id, codigo, texto, clase, area,"
                " causa, actuacion, criticidad) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    planta_id, a["codigo"], a["texto"], a["clase"],
                    a["area"], a["causa"], a["actuacion"], a["criticidad"],
                ),
            )
            nuevas += 1

    con.commit()
    return {"nuevas": nuevas, "actualizadas": actualizadas, "leidas": len(alarmas)}
