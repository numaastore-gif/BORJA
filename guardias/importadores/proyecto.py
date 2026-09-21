"""Metadatos de un proyecto archivado (.zap / .zip).

Los archivos de proyecto son binarios y pesados: aquí **no** se guarda el
contenido en la base ni en el repositorio, solo su huella, su inventario de
ficheros y lo que se pueda deducir de la versión y de las estaciones. El
archivo original se queda donde esté y se referencia por ruta.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

# Extensiones de archivado de TIA Portal: .zap13 -> V13, .zap17 -> V17...
_RE_ZAP = re.compile(r"\.zap(\d{2})$", re.IGNORECASE)


def _sha256(ruta: Path, bloque: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with ruta.open("rb") as f:
        for trozo in iter(lambda: f.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def _version_desde_nombre(ruta: Path) -> str | None:
    m = _RE_ZAP.search(ruta.name)
    return f"TIA Portal V{m.group(1)}" if m else None


def _leer_entradas(ruta: Path) -> list[dict]:
    if not zipfile.is_zipfile(ruta):
        return []
    with zipfile.ZipFile(ruta) as z:
        return [
            {
                "ruta": info.filename,
                "tam_bytes": info.file_size,
                "modificado": datetime(*info.date_time).isoformat(timespec="seconds"),
            }
            for info in z.infolist()
            if not info.is_dir()
        ]


def _deducir_version(entradas: list[dict], ruta: Path) -> str | None:
    """Versión del entorno de ingeniería, por extensión o por contenido."""
    por_nombre = _version_desde_nombre(ruta)
    if por_nombre:
        return por_nombre
    nombres = [e["ruta"].lower() for e in entradas]
    if any(n.endswith(".s7p") for n in nombres):
        return "STEP7 V5 / PCS7"
    if any("/system/" in n and n.endswith(".ap") for n in nombres):
        return "TIA Portal"
    return None


def _deducir_estaciones(entradas: list[dict]) -> list[str]:
    """Nombres de las carpetas de primer nivel, que suelen ser las estaciones."""
    raices = {e["ruta"].split("/", 1)[0] for e in entradas if "/" in e["ruta"]}
    return sorted(r for r in raices if r)


def leer_metadatos_archivo(ruta: Path | str) -> dict:
    """Huella e inventario de un archivo de proyecto, sin escribir en la base."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise FileNotFoundError(ruta)
    entradas = _leer_entradas(ruta)
    return {
        "nombre": ruta.stem,
        "ruta_archivo": str(ruta.resolve()),
        "sha256": _sha256(ruta),
        "tam_bytes": ruta.stat().st_size,
        "fecha_version": datetime.fromtimestamp(ruta.stat().st_mtime).isoformat(
            timespec="seconds"
        ),
        "version_pcs7": _deducir_version(entradas, ruta),
        "estaciones": _deducir_estaciones(entradas),
        "entradas": entradas,
    }


def importar_proyecto(
    con: sqlite3.Connection,
    planta_id: int,
    ruta: Path | str,
    *,
    nombre: str | None = None,
    origen: str | None = None,
    notas: str | None = None,
) -> dict:
    """Registra el archivo de proyecto y su inventario de ficheros.

    Si ya hay un proyecto con la misma huella para esa planta no se duplica:
    se devuelve el existente, porque es literalmente la misma copia.
    """
    meta = leer_metadatos_archivo(ruta)

    ya = con.execute(
        "SELECT id FROM proyecto WHERE planta_id = ? AND sha256 = ?",
        (planta_id, meta["sha256"]),
    ).fetchone()
    if ya:
        return {"proyecto_id": int(ya["id"]), "duplicado": True, **meta}

    cur = con.execute(
        "INSERT INTO proyecto (planta_id, nombre, version_pcs7, ruta_archivo,"
        " sha256, tam_bytes, fecha_version, origen, notas)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            planta_id,
            nombre or meta["nombre"],
            meta["version_pcs7"],
            meta["ruta_archivo"],
            meta["sha256"],
            meta["tam_bytes"],
            meta["fecha_version"],
            origen,
            notas,
        ),
    )
    proyecto_id = int(cur.lastrowid)
    con.executemany(
        "INSERT INTO proyecto_entrada (proyecto_id, ruta, tam_bytes, modificado)"
        " VALUES (?, ?, ?, ?)",
        [
            (proyecto_id, e["ruta"], e["tam_bytes"], e["modificado"])
            for e in meta["entradas"]
        ],
    )
    con.commit()
    return {"proyecto_id": proyecto_id, "duplicado": False, **meta}
