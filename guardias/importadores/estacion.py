"""Lectura de la carpeta de un multiproyecto STEP7 / PCS7.

Aunque el contenido del programa está en binario, la carpeta del multiproyecto
trae dos ficheros que sí se leen y que son justo lo que hace falta para la
ficha de planta:

* ``ApiLog/Step7Bas.ver`` -- inventario del software instalado en la estación
  de ingeniería, con sus versiones y service packs.
* ``s7extref/s7envref.xml`` -- los proyectos que cuelgan del multiproyecto, con
  el nombre de la estación y la ruta local de cada ``.s7p``.
"""

from __future__ import annotations

import re
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

from .texto import decodificar

# Se reconoce primero lo que es una versión y se da por nombre todo lo demás.
# Al revés no funciona: "V7.4 + SP1 + Upd4" lleva tres letras seguidas en
# "Upd" y pasaría por nombre de producto, dejando al suyo sin versión.
_RE_VERSION = re.compile(
    r"[VK]?\d[\d.]*"                                    # 5.6, V09.00.01.00, K7.4.1.4
    r"(?:\s*\+?\s*(?:SP|Upd|HF|Update|Hotfix)\s*\d+)*"  # + SP1 + Upd4, SP3
    r"(?:_[\d.]+)*",                                     # _01.44.00.02
    re.IGNORECASE,
)

# Productos que interesan en la ficha; el resto son componentes internos.
RELEVANTES = (
    "STEP 7", "SIMATIC PCS 7", "WinCC", "DOCPRO", "Drive ES", "S7-PLCSIM",
    "Automation License Manager", "SIMATIC BATCH", "SIMATIC Route Control",
    "IEAPO", "SIMOTION", "Version Trail", "SIMATIC NET",
)


def _cadenas(datos: bytes) -> list[str]:
    """Extrae las cadenas del fichero de versiones.

    Van prefijadas por un byte con su longitud, así que se leen contando y no
    buscando: si se busca por patrón, el byte de longitud de una cadena se
    cuela como carácter al final de la anterior y los nombres salen pegados a
    la versión del producto de arriba.
    """
    salida: list[str] = []
    i, fin = 0, len(datos)
    while i < fin:
        largo = datos[i]
        if 3 <= largo <= 127 and i + 1 + largo <= fin:
            bruto = datos[i + 1 : i + 1 + largo]
            if all(0x20 <= b < 0xFF for b in bruto):
                texto = decodificar(bruto).strip()
                if texto and texto.isprintable():
                    salida.append(texto)
                    i += 1 + largo
                    continue
        i += 1
    return salida


def parsear_versiones(datos: bytes | str) -> list[dict]:
    """Devuelve los productos instalados y su versión.

    El fichero alterna nombre de producto y una o varias cadenas de versión;
    se toma como versión la primera que sigue a cada nombre.
    """
    if isinstance(datos, str):
        datos = datos.encode("latin-1")

    productos: list[dict] = []
    for cadena in _cadenas(datos):
        if not _RE_VERSION.fullmatch(cadena):
            productos.append({"producto": cadena, "version": None})
        elif productos and productos[-1]["version"] is None:
            productos[-1]["version"] = cadena
    return [p for p in productos if p["version"]]


def solo_relevantes(productos: list[dict]) -> list[dict]:
    return [p for p in productos if any(r.lower() in p["producto"].lower() for r in RELEVANTES)]


def parsear_referencias(datos: bytes | str) -> list[dict]:
    """Proyectos del multiproyecto, leídos de ``s7envref.xml``."""
    texto = decodificar(datos) if isinstance(datos, bytes) else datos
    raiz = ET.fromstring(texto)
    return [
        {
            "nombre": env.get("env_name"),
            "estacion": env.get("host_name"),
            "ruta": env.get("local_path"),
        }
        for env in raiz.findall("env")
    ]


def leer_multiproyecto(carpeta: Path | str) -> dict:
    """Resume la carpeta de un multiproyecto, mire donde mire dentro de ella."""
    carpeta = Path(carpeta)
    resumen: dict = {
        "nombre": None, "estacion_ingenieria": None,
        "software": [], "proyectos": [], "vacio": True,
    }

    ver = next(carpeta.rglob("Step7Bas.ver"), None)
    if ver is not None:
        resumen["software"] = parsear_versiones(ver.read_bytes())
        resumen["nombre"] = ver.parent.parent.name

    envref = next(carpeta.rglob("s7envref.xml"), None)
    if envref is not None:
        resumen["proyectos"] = parsear_referencias(envref.read_bytes())
        estaciones = {p["estacion"] for p in resumen["proyectos"] if p["estacion"]}
        if len(estaciones) == 1:
            resumen["estacion_ingenieria"] = estaciones.pop()

    # El multiproyecto lleva contenido de verdad solo si hay un .s7p dentro.
    resumen["vacio"] = not any(carpeta.rglob("*.s7p"))
    return resumen


def importar_estacion(
    con: sqlite3.Connection, planta_id: int, carpeta: Path | str, *, todo: bool = False
) -> dict:
    """Vuelca el software de la estación de ingeniería en la ficha de la planta.

    Con ``todo`` se guardan los 70 y pico componentes; por defecto solo los
    productos que se consultan durante una guardia.
    """
    resumen = leer_multiproyecto(carpeta)
    software = resumen["software"] if todo else solo_relevantes(resumen["software"])

    nuevos = 0
    for p in software:
        # La clave incluye la versión: una estación puede tener instaladas dos
        # versiones de la misma librería (V7.1 heredada y V9.0 actual), y
        # perder una de las dos despista justo cuando hace falta saberlo.
        ya = con.execute(
            "SELECT id FROM software WHERE planta_id = ? AND producto = ? AND version IS ?",
            (planta_id, p["producto"], p["version"]),
        ).fetchone()
        if not ya:
            con.execute(
                "INSERT INTO software (planta_id, producto, version, notas)"
                " VALUES (?, ?, ?, ?)",
                (planta_id, p["producto"], p["version"],
                 f"Leído de {resumen['estacion_ingenieria'] or 'la estación de ingeniería'}"),
            )
            nuevos += 1
    con.commit()
    return {**resumen, "guardados": len(software), "nuevos": nuevos}
