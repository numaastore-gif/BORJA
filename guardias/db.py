"""Acceso a la base de datos SQLite."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable

RAIZ = Path(__file__).resolve().parent.parent
ESQUEMA = Path(__file__).resolve().parent / "schema.sql"


def ruta_bd() -> Path:
    """Ruta del fichero SQLite. Configurable con GUARDIAS_BD."""
    return Path(os.environ.get("GUARDIAS_BD", RAIZ / "datos" / "guardias.db"))


def ruta_adjuntos() -> Path:
    return Path(os.environ.get("GUARDIAS_ADJUNTOS", RAIZ / "datos" / "adjuntos"))


def conectar(ruta: Path | str | None = None) -> sqlite3.Connection:
    destino = Path(ruta) if ruta else ruta_bd()
    if str(destino) != ":memory:":
        destino.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(destino, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
    return con


def inicializar(con: sqlite3.Connection) -> None:
    con.executescript(ESQUEMA.read_text(encoding="utf-8"))
    con.commit()


def abrir(ruta: Path | str | None = None) -> sqlite3.Connection:
    """Conecta y asegura que el esquema existe."""
    con = conectar(ruta)
    inicializar(con)
    return con


# ------------------------------------------------------------------ utilidades


def insertar(con: sqlite3.Connection, tabla: str, datos: dict[str, Any]) -> int:
    datos = {k: v for k, v in datos.items() if v is not None}
    columnas = ", ".join(datos)
    marcas = ", ".join("?" * len(datos))
    cur = con.execute(
        f"INSERT INTO {tabla} ({columnas}) VALUES ({marcas})", list(datos.values())
    )
    con.commit()
    return int(cur.lastrowid)


def actualizar(
    con: sqlite3.Connection, tabla: str, id_: int, datos: dict[str, Any]
) -> None:
    if not datos:
        return
    asignaciones = ", ".join(f"{k} = ?" for k in datos)
    if _tiene_columna(con, tabla, "actualizado"):
        asignaciones += ", actualizado = datetime('now')"
    con.execute(
        f"UPDATE {tabla} SET {asignaciones} WHERE id = ?", [*datos.values(), id_]
    )
    con.commit()


def borrar(con: sqlite3.Connection, tabla: str, id_: int) -> None:
    con.execute(f"DELETE FROM {tabla} WHERE id = ?", (id_,))
    con.commit()


def uno(con: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
    return con.execute(sql, tuple(params)).fetchone()


def todos(con: sqlite3.Connection, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
    return con.execute(sql, tuple(params)).fetchall()


def _tiene_columna(con: sqlite3.Connection, tabla: str, columna: str) -> bool:
    filas = con.execute(f"PRAGMA table_info({tabla})").fetchall()
    return any(f["name"] == columna for f in filas)
