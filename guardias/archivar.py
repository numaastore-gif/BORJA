"""Localiza el archivado más reciente de un proyecto y lo trae a la herramienta.

Pensado para los directorios de proyecto del cliente, del estilo:

    \\\\10.103.160.72\\Proyectos\\Maval\\C700\\Dosificado\\PLC

Uso típico desde tu equipo, con el recurso de red accesible:

    python -m guardias.archivar "\\\\10.103.160.72\\Proyectos\\Maval\\C700\\Dosificado\\PLC" \\
        --planta C700 --extraer

Por defecto solo mira: enumera lo que ha encontrado y no toca nada.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
import zipfile
from datetime import date, datetime
from pathlib import Path

from .db import abrir, ruta_adjuntos, uno
from .importadores import importar_proyecto, importar_simbolos

PATRONES = ("*.zap*", "*.zip", "*.s7p", "*.7z", "*.rar")
# Extensiones de tabla de símbolos que se importan solas al extraer.
EXT_SIMBOLOS = (".asc", ".sdf", ".seq")

# Fechas tal y como aparecen en los nombres de archivado, de más a menos
# específica. El año de dos cifras se interpreta como 20xx.
_FORMATOS = (
    # aaaammdd: 20260911, 2026-09-11, 2026_09_11
    (re.compile(r"(20\d{2})[-_.]?(\d{2})[-_.]?(\d{2})"), ("a", "m", "d")),
    # ddmmaaaa pegado, la convención de C700_DOSE_11092026
    (re.compile(r"(?<!\d)(\d{2})(\d{2})(20\d{2})(?!\d)"), ("d", "m", "a")),
    # dd-mm-aaaa con separadores
    (re.compile(r"(\d{2})[-_.](\d{2})[-_.](20\d{2})"), ("d", "m", "a")),
    # ddmmaa de dos cifras
    (re.compile(r"(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)"), ("d", "m", "a2")),
)


def fecha_de_nombre(nombre: str) -> date | None:
    """Extrae la fecha del nombre del archivado, si la lleva."""
    for regex, orden in _FORMATOS:
        m = regex.search(nombre)
        if not m:
            continue
        partes = dict(zip(orden, m.groups()))
        try:
            anio = int(partes.get("a") or f"20{partes['a2']}")
            return date(anio, int(partes["m"]), int(partes["d"]))
        except (ValueError, KeyError):
            continue
    return None


def candidatos(directorio: Path | str, patrones: tuple[str, ...] = PATRONES) -> list[dict]:
    """Archivados del directorio, del más reciente al más antiguo.

    Se ordena por la fecha del nombre cuando la lleva y, si no, por la fecha de
    modificación: en estos directorios el nombre es más fiable que el mtime,
    que se altera al copiar entre unidades de red.
    """
    directorio = Path(directorio)
    if not directorio.is_dir():
        raise NotADirectoryError(directorio)

    encontrados = []
    for patron in patrones:
        for ruta in directorio.glob(patron):
            if not ruta.is_file():
                continue
            estado = ruta.stat()
            modificado = datetime.fromtimestamp(estado.st_mtime)
            del_nombre = fecha_de_nombre(ruta.name)
            encontrados.append(
                {
                    "ruta": ruta,
                    "nombre": ruta.name,
                    "tam_bytes": estado.st_size,
                    "modificado": modificado,
                    "fecha_nombre": del_nombre,
                    "fecha": del_nombre or modificado.date(),
                }
            )
    encontrados.sort(key=lambda c: (c["fecha"], c["modificado"]), reverse=True)
    return encontrados


def _destino_seguro(base: Path, nombre_interno: str) -> Path:
    """Evita que una entrada del archivo escriba fuera del directorio destino.

    Los archivados vienen del cliente y no se han generado aquí, así que no se
    da por bueno lo que digan sus rutas internas.
    """
    destino = (base / nombre_interno).resolve()
    if not destino.is_relative_to(base.resolve()):
        raise ValueError(f"ruta fuera del destino: {nombre_interno}")
    return destino


def extraer(ruta: Path | str, destino: Path | str) -> Path:
    """Descomprime el archivado en ``destino/<nombre>`` y devuelve esa carpeta."""
    ruta, destino = Path(ruta), Path(destino)
    if not zipfile.is_zipfile(ruta):
        raise ValueError(
            f"{ruta.name} no es un zip. Los .7z, .rar y los archivados "
            "autoextraíbles hay que abrirlos con su propia herramienta."
        )

    carpeta = destino / ruta.stem
    carpeta.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ruta) as z:
        for info in z.infolist():
            salida = _destino_seguro(carpeta, info.filename)
            if info.is_dir():
                salida.mkdir(parents=True, exist_ok=True)
                continue
            salida.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as origen, salida.open("wb") as fichero:
                shutil.copyfileobj(origen, fichero)
    return carpeta


def tablas_de_simbolos(carpeta: Path | str) -> list[Path]:
    carpeta = Path(carpeta)
    return sorted(
        r for r in carpeta.rglob("*") if r.is_file() and r.suffix.lower() in EXT_SIMBOLOS
    )


def resolver_planta(con: sqlite3.Connection, referencia: str) -> int:
    """Acepta el código o el id de la planta y devuelve el id."""
    fila = uno(con, "SELECT id FROM planta WHERE codigo = ?", (referencia,))
    if fila:
        return int(fila["id"])
    if referencia.isdigit() and uno(con, "SELECT id FROM planta WHERE id = ?", (referencia,)):
        return int(referencia)
    codigos = [f["codigo"] for f in con.execute("SELECT codigo FROM planta ORDER BY codigo")]
    raise SystemExit(
        f"No existe la planta «{referencia}». Dadas de alta: {', '.join(codigos) or 'ninguna'}.\n"
        "Créala en la interfaz web o pasa --crear-planta «Nombre de la planta»."
    )


def _tabla(filas: list[dict]) -> str:
    lineas = []
    for i, c in enumerate(filas):
        marca = "→" if i == 0 else " "
        origen = "nombre" if c["fecha_nombre"] else "mtime"
        lineas.append(
            f" {marca} {c['fecha']}  ({origen:6})  "
            f"{c['tam_bytes'] / 1048576:8.1f} MB  {c['nombre']}"
        )
    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directorio", help="carpeta con los archivados del proyecto")
    parser.add_argument("--planta", help="código o id de la planta ya dada de alta")
    parser.add_argument("--crear-planta", metavar="NOMBRE",
                        help="da de alta la planta con --planta como código")
    parser.add_argument("--extraer", action="store_true",
                        help="descomprime el archivado elegido")
    parser.add_argument("--copiar", action="store_true",
                        help="copia el archivado a datos/adjuntos (ojo al tamaño)")
    parser.add_argument("--destino", help="carpeta donde extraer (por defecto datos/proyectos)")
    parser.add_argument("--nombre", help="nombre del archivado a usar en vez del más reciente")
    args = parser.parse_args(argv)

    try:
        encontrados = candidatos(args.directorio)
    except NotADirectoryError:
        print(f"No se puede abrir {args.directorio}.")
        print("Comprueba que el recurso de red está montado y que tienes permiso.")
        return 1

    if not encontrados:
        print(f"No hay archivados ({', '.join(PATRONES)}) en {args.directorio}.")
        return 1

    print(f"{len(encontrados)} archivados en {args.directorio}:\n{_tabla(encontrados)}\n")

    if args.nombre:
        elegido = next((c for c in encontrados if c["nombre"] == args.nombre), None)
        if elegido is None:
            print(f"No está «{args.nombre}» en ese directorio.")
            return 1
    else:
        elegido = encontrados[0]

    if not args.planta:
        print("Elige planta con --planta CODIGO para registrarlo. Solo se ha listado.")
        return 0

    con = abrir()
    if args.crear_planta:
        from .db import insertar

        con.execute(
            "INSERT OR IGNORE INTO planta (codigo, nombre) VALUES (?, ?)",
            (args.planta, args.crear_planta),
        )
        con.commit()
    planta_id = resolver_planta(con, args.planta)

    ruta = elegido["ruta"]
    if args.copiar:
        carpeta = ruta_adjuntos() / "proyectos" / str(planta_id)
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta = Path(shutil.copy2(ruta, carpeta / ruta.name))
        print(f"Copiado a {ruta}")

    resultado = importar_proyecto(con, planta_id, ruta, origen=args.directorio)
    estado = "ya estaba registrado" if resultado["duplicado"] else "registrado"
    print(
        f"Proyecto {estado}: id {resultado['proyecto_id']}"
        f"{' · ' + resultado['version_pcs7'] if resultado['version_pcs7'] else ''}"
        f" · {len(resultado['entradas'])} ficheros"
    )
    if resultado["estaciones"]:
        print(f"Estaciones: {', '.join(resultado['estaciones'])}")

    if args.extraer:
        destino = Path(args.destino) if args.destino else ruta_adjuntos() / "proyectos_extraidos"
        try:
            carpeta = extraer(ruta, destino)
        except ValueError as error:
            print(f"No se ha extraído: {error}")
            return 1
        print(f"Extraído en {carpeta}")

        tablas = tablas_de_simbolos(carpeta)
        if tablas:
            total = 0
            for n, tabla in enumerate(tablas):
                # Solo la primera reemplaza; las demás se acumulan.
                total += importar_simbolos(
                    con, resultado["proyecto_id"], tabla.read_bytes(), reemplazar=(n == 0)
                )["importados"]
            print(f"Símbolos importados: {total} de {len(tablas)} tablas.")

    print(f"\nFicha: http://127.0.0.1:8000/proyectos/{resultado['proyecto_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
