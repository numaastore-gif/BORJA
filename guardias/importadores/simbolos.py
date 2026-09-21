"""Importación de tablas de símbolos de STEP7 / PCS7.

Admite los tres formatos con los que suele salir la tabla de símbolos:

* ``.asc``  -- registro de 126 caracteres precedido de ``126,`` (ancho fijo).
* ``.sdf``  -- CSV entrecomillado de cuatro campos.
* ``.csv`` / ``.txt`` -- delimitado por tabulador, ``;`` o ``,``, con o sin
  fila de cabecera.
"""

from __future__ import annotations

import re
import sqlite3

from .texto import celda, decodificar, leer_filas, mapear_columnas, parece_cabecera

# Anchos del registro ASC de STEP7: nombre, operando, tipo, comentario.
ANCHOS_ASC = (24, 12, 10, 80)

ALIAS = {
    "nombre": ("symbol", "symbolname", "simbolo", "nombre", "name", "variable"),
    "direccion": ("address", "adresse", "operand", "direccion", "operando"),
    "tipo_dato": ("data type", "datentyp", "datatype", "tipo", "tipo de datos"),
    "comentario": ("comment", "kommentar", "comentario", "descripcion"),
}


def _limpiar(valor: str) -> str | None:
    """Colapsa los espacios internos del relleno de ancho fijo."""
    valor = re.sub(r"\s+", " ", valor).strip()
    return valor or None


def _parsear_asc(texto: str) -> list[dict]:
    simbolos = []
    for linea in texto.splitlines():
        if not linea.startswith("126,"):
            continue
        resto = linea[4:]
        campos, pos = [], 0
        for ancho in ANCHOS_ASC:
            campos.append(resto[pos : pos + ancho])
            pos += ancho
        nombre, direccion, tipo, comentario = (_limpiar(c) for c in campos)
        if nombre:
            simbolos.append(
                {
                    "nombre": nombre,
                    "direccion": direccion,
                    "tipo_dato": tipo,
                    "comentario": comentario,
                }
            )
    return simbolos


def _parsear_delimitado(texto: str) -> list[dict]:
    filas = leer_filas(texto)
    if not filas:
        return []

    if parece_cabecera(filas[0], ALIAS):
        mapa = mapear_columnas(filas[0], ALIAS)
        cuerpo = filas[1:]
    else:
        # Sin cabecera se asume el orden nativo de STEP7.
        mapa = {"nombre": 0, "direccion": 1, "tipo_dato": 2, "comentario": 3}
        cuerpo = filas

    simbolos = []
    for fila in cuerpo:
        nombre = celda(fila, mapa, "nombre")
        if not nombre:
            continue
        simbolos.append(
            {
                "nombre": _limpiar(nombre),
                "direccion": _limpiar(celda(fila, mapa, "direccion") or ""),
                "tipo_dato": _limpiar(celda(fila, mapa, "tipo_dato") or ""),
                "comentario": _limpiar(celda(fila, mapa, "comentario") or ""),
            }
        )
    return simbolos


def parsear_simbolos(datos: bytes | str) -> list[dict]:
    """Devuelve la lista de símbolos de una exportación, sin tocar la base."""
    texto = decodificar(datos) if isinstance(datos, bytes) else datos
    if any(ln.startswith("126,") for ln in texto.splitlines()[:50]):
        return _parsear_asc(texto)
    return _parsear_delimitado(texto)


def importar_simbolos(
    con: sqlite3.Connection, proyecto_id: int, datos: bytes | str, *, reemplazar: bool = True
) -> dict:
    """Carga la tabla de símbolos de un proyecto.

    Con ``reemplazar`` se borra la tabla anterior del proyecto, que es lo
    normal al subir una versión nueva del programa.
    """
    simbolos = parsear_simbolos(datos)
    if reemplazar:
        con.execute("DELETE FROM simbolo WHERE proyecto_id = ?", (proyecto_id,))
    con.executemany(
        "INSERT INTO simbolo (proyecto_id, nombre, direccion, tipo_dato, comentario)"
        " VALUES (?, ?, ?, ?, ?)",
        [
            (
                proyecto_id,
                s["nombre"],
                s["direccion"],
                s["tipo_dato"],
                s["comentario"],
            )
            for s in simbolos
        ],
    )
    con.commit()
    return {"importados": len(simbolos), "reemplazado": reemplazar}
