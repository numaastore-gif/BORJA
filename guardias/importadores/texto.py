"""Lectura tolerante de exportaciones de texto de Siemens.

Las exportaciones de STEP7/WinCC llegan en codificaciones y delimitadores muy
variados según la versión y el idioma de la estación de ingeniería, así que
aquí se detecta todo en vez de exigir un formato concreto.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata

CODIFICACIONES = ("utf-8-sig", "utf-16", "cp1252", "latin-1")
DELIMITADORES = ("\t", ";", ",", "|")


def decodificar(datos: bytes) -> str:
    """Devuelve el texto probando las codificaciones habituales de Siemens."""
    if datos.startswith((b"\xff\xfe", b"\xfe\xff")):
        return datos.decode("utf-16")
    for codec in CODIFICACIONES:
        try:
            return datos.decode(codec)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return datos.decode("latin-1", errors="replace")


def detectar_delimitador(texto: str) -> str:
    """Delimitador más consistente entre las primeras líneas no vacías."""
    lineas = [ln for ln in texto.splitlines() if ln.strip()][:20]
    if not lineas:
        return "\t"
    mejor, mejor_puntuacion = "\t", -1.0
    for delim in DELIMITADORES:
        cuentas = [ln.count(delim) for ln in lineas]
        if not any(cuentas):
            continue
        media = sum(cuentas) / len(cuentas)
        # Premia el delimitador frecuente y estable en todas las líneas.
        varianza = sum((c - media) ** 2 for c in cuentas) / len(cuentas)
        puntuacion = media - varianza
        if puntuacion > mejor_puntuacion:
            mejor, mejor_puntuacion = delim, puntuacion
    return mejor


def leer_filas(texto: str, delimitador: str | None = None) -> list[list[str]]:
    delim = delimitador or detectar_delimitador(texto)
    lector = csv.reader(io.StringIO(texto), delimiter=delim, quotechar='"')
    filas = []
    for fila in lector:
        celdas = [c.strip() for c in fila]
        if any(celdas):
            filas.append(celdas)
    return filas


def normalizar(cabecera: str) -> str:
    """Minúsculas sin acentos ni signos, para comparar nombres de columna."""
    sin_acentos = "".join(
        c
        for c in unicodedata.normalize("NFD", cabecera)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", "", sin_acentos.lower())


def mapear_columnas(cabeceras: list[str], alias: dict[str, tuple[str, ...]]) -> dict[str, int]:
    """Asocia cada campo del modelo con el índice de columna que le corresponde.

    ``alias`` lleva, por campo, los nombres posibles de la columna en alemán,
    inglés y español (los tres idiomas en que suelen venir los ficheros).
    """
    normalizadas = [normalizar(c) for c in cabeceras]
    mapa: dict[str, int] = {}
    for campo, nombres in alias.items():
        candidatos = [normalizar(n) for n in nombres]
        for i, cab in enumerate(normalizadas):
            if i in mapa.values():
                continue
            if cab in candidatos or any(cab.startswith(c) for c in candidatos if c):
                mapa[campo] = i
                break
    return mapa


def parece_cabecera(fila: list[str], alias: dict[str, tuple[str, ...]]) -> bool:
    """True si la fila contiene al menos dos nombres de columna conocidos."""
    conocidos = {normalizar(n) for nombres in alias.values() for n in nombres}
    aciertos = sum(1 for c in fila if normalizar(c) in conocidos)
    return aciertos >= 2


def celda(fila: list[str], mapa: dict[str, int], campo: str) -> str | None:
    i = mapa.get(campo)
    if i is None or i >= len(fila):
        return None
    valor = fila[i].strip()
    return valor or None
