"""Consultas del dominio: lo que hace falta mirar durante una guardia."""

from __future__ import annotations

import re
import sqlite3
from typing import Any

from .db import todos, uno

ESTADOS_ABIERTOS = ("abierta", "en curso", "seguimiento")


# --------------------------------------------------------------------- panel


def guardia_activa(con: sqlite3.Connection) -> sqlite3.Row | None:
    return uno(
        con,
        "SELECT * FROM guardia WHERE datetime('now','localtime') BETWEEN inicio AND fin"
        " ORDER BY inicio LIMIT 1",
    )


def proxima_guardia(con: sqlite3.Connection) -> sqlite3.Row | None:
    return uno(
        con, "SELECT * FROM guardia WHERE inicio > datetime('now','localtime') ORDER BY inicio LIMIT 1"
    )


def incidencias_abiertas(con: sqlite3.Connection, limite: int = 50) -> list[sqlite3.Row]:
    marcas = ", ".join("?" * len(ESTADOS_ABIERTOS))
    return todos(
        con,
        "SELECT i.*, p.nombre AS planta, p.codigo AS planta_codigo"
        " FROM incidencia i JOIN planta p ON p.id = i.planta_id"
        f" WHERE i.estado IN ({marcas})"
        " ORDER BY CASE i.criticidad WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END,"
        " i.recibido DESC LIMIT ?",
        (*ESTADOS_ABIERTOS, limite),
    )


def resumen(con: sqlite3.Connection) -> dict[str, Any]:
    def escalar(sql: str, params: tuple = ()) -> int:
        fila = uno(con, sql, params)
        return int(fila[0]) if fila and fila[0] is not None else 0

    marcas = ", ".join("?" * len(ESTADOS_ABIERTOS))
    return {
        "plantas": escalar("SELECT count(*) FROM planta"),
        "alarmas": escalar("SELECT count(*) FROM alarma"),
        "abiertas": escalar(
            f"SELECT count(*) FROM incidencia WHERE estado IN ({marcas})",
            ESTADOS_ABIERTOS,
        ),
        "ultimos_30d": escalar(
            "SELECT count(*) FROM incidencia WHERE recibido >= datetime('now','localtime','-30 day')"
        ),
        "parada_30d": escalar(
            "SELECT coalesce(sum(parada_min),0) FROM incidencia"
            " WHERE recibido >= datetime('now','localtime','-30 day')"
        ),
    }


def actividad_por_planta(con: sqlite3.Connection, dias: int = 90) -> list[sqlite3.Row]:
    """Ranking de plantas por avisos recientes: dónde se está yendo el tiempo."""
    return todos(
        con,
        "SELECT p.id, p.codigo, p.nombre, count(i.id) AS avisos,"
        " coalesce(sum(i.parada_min),0) AS parada,"
        " sum(CASE WHEN i.resuelto_remoto THEN 1 ELSE 0 END) AS remotas"
        " FROM planta p LEFT JOIN incidencia i"
        "   ON i.planta_id = p.id AND i.recibido >= datetime('now','localtime', ?)"
        " GROUP BY p.id ORDER BY avisos DESC, p.codigo",
        (f"-{int(dias)} day",),
    )


# -------------------------------------------------------------------- fichas


def ficha_planta(con: sqlite3.Connection, planta_id: int) -> dict[str, Any] | None:
    planta = uno(con, "SELECT * FROM planta WHERE id = ?", (planta_id,))
    if planta is None:
        return None
    return {
        "planta": planta,
        "contactos": todos(
            con,
            "SELECT * FROM contacto WHERE planta_id = ? ORDER BY prioridad, nombre",
            (planta_id,),
        ),
        "equipos": todos(
            con, "SELECT * FROM equipo WHERE planta_id = ? ORDER BY tipo, nombre", (planta_id,)
        ),
        "software": todos(
            con, "SELECT * FROM software WHERE planta_id = ? ORDER BY producto", (planta_id,)
        ),
        "proyectos": todos(
            con,
            "SELECT p.*, (SELECT count(*) FROM simbolo s WHERE s.proyecto_id = p.id)"
            " AS simbolos FROM proyecto p WHERE planta_id = ?"
            " ORDER BY coalesce(fecha_version, creado) DESC",
            (planta_id,),
        ),
        "alarmas": todos(
            con,
            "SELECT * FROM alarma WHERE planta_id = ? ORDER BY codigo LIMIT 200",
            (planta_id,),
        ),
        "incidencias": todos(
            con,
            "SELECT * FROM incidencia WHERE planta_id = ? ORDER BY recibido DESC LIMIT 50",
            (planta_id,),
        ),
    }


def listar_incidencias(
    con: sqlite3.Connection,
    *,
    planta_id: int | None = None,
    estado: str | None = None,
    limite: int = 200,
) -> list[sqlite3.Row]:
    sql = (
        "SELECT i.*, p.nombre AS planta, p.codigo AS planta_codigo"
        " FROM incidencia i JOIN planta p ON p.id = i.planta_id WHERE 1=1"
    )
    params: list[Any] = []
    if planta_id:
        sql += " AND i.planta_id = ?"
        params.append(planta_id)
    if estado:
        sql += " AND i.estado = ?"
        params.append(estado)
    sql += " ORDER BY i.recibido DESC LIMIT ?"
    params.append(limite)
    return todos(con, sql, params)


def reincidencias(con: sqlite3.Connection, incidencia: sqlite3.Row) -> list[sqlite3.Row]:
    """Avisos parecidos anteriores en la misma planta: el atajo de la guardia."""
    return buscar(
        con,
        incidencia["titulo"],
        entidad="incidencia",
        limite=6,
        excluir_id=incidencia["id"],
        planta_id=incidencia["planta_id"],
        flexible=True,
    )


# ------------------------------------------------------------------ búsqueda

_RE_PALABRA = re.compile(r"[\wáéíóúüñÁÉÍÓÚÜÑ]+", re.UNICODE)


def consulta_fts(texto: str, *, flexible: bool = False) -> str:
    """Convierte lo que se teclea en una consulta FTS5 segura.

    El operario dicta el texto de la alarma tal cual, con comillas, guiones y
    signos que FTS5 interpretaría como sintaxis; se quedan solo las palabras y
    a la última se le añade ``*`` para que busque mientras escribes.

    Con ``flexible`` las palabras se unen con OR en vez de exigirlas todas. Es
    lo que hace falta al diagnosticar: el texto pegado del SCADA nunca coincide
    palabra por palabra con el título que escribiste tú en un aviso de hace
    tres meses, y exigiéndolas todas ese aviso no aparece nunca. El orden por
    relevancia ya deja arriba los que coinciden en más palabras.
    """
    palabras = _RE_PALABRA.findall(texto or "")
    if not palabras:
        return ""
    terminos = [f'"{p}"' for p in palabras[:-1]]
    terminos.append(f'"{palabras[-1]}"*')
    return (" OR " if flexible else " ").join(terminos)


def buscar(
    con: sqlite3.Connection,
    texto: str,
    *,
    entidad: str | None = None,
    limite: int = 40,
    excluir_id: int | None = None,
    planta_id: int | None = None,
    flexible: bool = False,
) -> list[sqlite3.Row]:
    """Busca en alarmas e incidencias por texto libre."""
    consulta = consulta_fts(texto, flexible=flexible)
    if not consulta:
        return []

    sql = (
        "SELECT b.entidad, b.entidad_id, b.titulo,"
        # Se marca con centinelas de control y no con HTML: el extracto sale
        # de texto que no controlamos, así que se escapa antes de resaltarlo.
        " snippet(busqueda, 3, char(2), char(3), '…', 20) AS extracto,"
        " bm25(busqueda) AS relevancia FROM busqueda b"
        " WHERE busqueda MATCH ?"
    )
    params: list[Any] = [consulta]
    if entidad:
        sql += " AND b.entidad = ?"
        params.append(entidad)
    if excluir_id is not None:
        sql += " AND NOT (b.entidad = ? AND b.entidad_id = ?)"
        params.extend([entidad or "incidencia", excluir_id])
    sql += " ORDER BY relevancia LIMIT ?"
    params.append(limite)

    filas = todos(con, sql, params)
    if planta_id is None:
        return filas
    return [f for f in filas if _planta_de(con, f["entidad"], f["entidad_id"]) == planta_id]


def _planta_de(con: sqlite3.Connection, entidad: str, entidad_id: int) -> int | None:
    tabla = "alarma" if entidad == "alarma" else "incidencia"
    fila = uno(con, f"SELECT planta_id FROM {tabla} WHERE id = ?", (entidad_id,))
    return fila["planta_id"] if fila else None


def buscar_simbolos(
    con: sqlite3.Connection, texto: str, *, proyecto_id: int | None = None, limite: int = 100
) -> list[sqlite3.Row]:
    """Busca una variable por nombre, dirección o comentario."""
    patron = f"%{texto.strip()}%"
    sql = (
        "SELECT s.*, p.nombre AS proyecto FROM simbolo s"
        " JOIN proyecto p ON p.id = s.proyecto_id"
        " WHERE (s.nombre LIKE ? OR s.direccion LIKE ? OR s.comentario LIKE ?)"
    )
    params: list[Any] = [patron, patron, patron]
    if proyecto_id:
        sql += " AND s.proyecto_id = ?"
        params.append(proyecto_id)
    sql += " ORDER BY s.nombre LIMIT ?"
    params.append(limite)
    return todos(con, sql, params)
