"""Resumen ligero de un proyecto PCS7, para poder compartirlo o consultarlo.

Un archivado de PCS7 son cientos de megas de binarios que no se pueden mandar
por ningún sitio ni leer de un vistazo. Esto recorre el archivo (o la carpeta
ya extraída) y saca solo lo que es texto y sirve para entender el programa:
estaciones, tablas de símbolos, listas de mensajes, bloques y pantallas.

    python -m guardias.radiografia "D:\\proyectos\\Dosificado_C700_20260918.zap"
    python -m guardias.radiografia <carpeta extraída> --salida ficha_C700.json

Genera un JSON con el detalle y un resumen en Markdown por pantalla.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Callable, Iterator

from .importadores import parsear_alarmas, parsear_simbolos
from .importadores.proyecto import leer_metadatos_archivo

# Extensiones que sí merece la pena abrir y leer.
EXT_SIMBOLOS = (".asc", ".sdf", ".seq")
EXT_LISTAS = (".csv", ".txt")
EXT_BLOQUES = (".scl", ".awl", ".cfc", ".sfc", ".gr7")
EXT_PANTALLAS = (".pdl", ".rdf", ".fwx")

# Un fichero de texto de más de esto no es una tabla de símbolos ni una lista
# de mensajes: no se abre, para no cargar medio proyecto en memoria.
LIMITE_LECTURA = 32 * 1024 * 1024

Entrada = tuple[str, int, Callable[[], bytes]]


def _entradas_zip(ruta: Path) -> Iterator[Entrada]:
    with zipfile.ZipFile(ruta) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            yield info.filename, info.file_size, lambda i=info: z.read(i)


def _entradas_carpeta(raiz: Path) -> Iterator[Entrada]:
    for fichero in sorted(raiz.rglob("*")):
        if fichero.is_file():
            relativa = fichero.relative_to(raiz).as_posix()
            yield relativa, fichero.stat().st_size, fichero.read_bytes


def entradas(origen: Path) -> Iterator[Entrada]:
    if origen.is_dir():
        return _entradas_carpeta(origen)
    if zipfile.is_zipfile(origen):
        return _entradas_zip(origen)
    raise ValueError(
        f"{origen.name} no es ni una carpeta ni un zip. Los .7z, .rar y los "
        "autoextraíbles hay que descomprimirlos antes y apuntar a la carpeta."
    )


def _es(ruta: str, extensiones: tuple[str, ...]) -> bool:
    return ruta.lower().endswith(extensiones)


def radiografiar(origen: Path | str, *, muestra: int = 15) -> dict:
    """Recorre el proyecto y devuelve su resumen.

    ``muestra`` es cuántas filas de cada tabla se incluyen como ejemplo: el
    objetivo es que el resultado quepa en un mensaje, no replicar el proyecto.
    """
    origen = Path(origen)
    resumen: dict = {
        "origen": str(origen),
        "tipo": "carpeta" if origen.is_dir() else "archivado",
        "extensiones": {},
        "estaciones": [],
        "proyectos_step7": [],
        "tablas_simbolos": [],
        "listas_mensajes": [],
        "bloques": [],
        "pantallas": [],
        "ficheros": 0,
        "tam_total": 0,
    }

    if not origen.is_dir():
        meta = leer_metadatos_archivo(origen)
        resumen["version_deducida"] = meta["version_pcs7"]
        resumen["sha256"] = meta["sha256"]
        resumen["tam_bytes"] = meta["tam_bytes"]

    extensiones: Counter[str] = Counter()
    raices: set[str] = set()

    for ruta, tam, leer in entradas(origen):
        resumen["ficheros"] += 1
        resumen["tam_total"] += tam
        extensiones[Path(ruta).suffix.lower() or "(sin extensión)"] += 1
        if "/" in ruta:
            raices.add(ruta.split("/", 1)[0])

        if _es(ruta, (".s7p",)):
            resumen["proyectos_step7"].append(ruta)
        elif _es(ruta, EXT_BLOQUES):
            resumen["bloques"].append(ruta)
        elif _es(ruta, EXT_PANTALLAS):
            resumen["pantallas"].append(ruta)

        if tam > LIMITE_LECTURA:
            continue

        if _es(ruta, EXT_SIMBOLOS):
            simbolos = parsear_simbolos(leer())
            if simbolos:
                resumen["tablas_simbolos"].append(
                    {"ruta": ruta, "simbolos": len(simbolos), "muestra": simbolos[:muestra]}
                )
        elif _es(ruta, EXT_LISTAS):
            alarmas = parsear_alarmas(leer())
            # Se acepta como lista de mensajes solo si la mayoría de filas
            # traen código: si no, es cualquier otro texto del proyecto.
            con_codigo = sum(1 for a in alarmas if a["codigo"])
            if len(alarmas) >= 5 and con_codigo >= len(alarmas) // 2:
                resumen["listas_mensajes"].append(
                    {"ruta": ruta, "alarmas": len(alarmas), "muestra": alarmas[:muestra]}
                )

    resumen["extensiones"] = dict(extensiones.most_common())
    resumen["estaciones"] = sorted(raices)
    # Las listas largas se recortan: el detalle ya está en el proyecto.
    for clave in ("bloques", "pantallas"):
        total = len(resumen[clave])
        resumen[f"total_{clave}"] = total
        resumen[clave] = sorted(resumen[clave])[: muestra * 4]
    return resumen


def a_markdown(r: dict) -> str:
    """Resumen legible, pensado para pegarlo en un mensaje."""
    lineas = [f"# Radiografía de {Path(r['origen']).name}", ""]

    lineas.append(f"- Tipo: {r['tipo']}")
    if r.get("version_deducida"):
        lineas.append(f"- Versión deducida: {r['version_deducida']}")
    if r.get("tam_bytes"):
        lineas.append(f"- Tamaño del archivado: {r['tam_bytes'] / 1048576:.1f} MB")
    lineas.append(f"- Ficheros: {r['ficheros']} ({r['tam_total'] / 1048576:.1f} MB sin comprimir)")
    if r["estaciones"]:
        lineas.append(f"- Estaciones / carpetas raíz: {', '.join(r['estaciones'])}")
    if r["proyectos_step7"]:
        lineas.append(f"- Proyectos STEP7: {', '.join(r['proyectos_step7'])}")
    lineas.append("")

    principales = list(r["extensiones"].items())[:15]
    lineas += ["## Contenido por extensión", ""]
    lineas += [f"- `{ext}`: {n}" for ext, n in principales]
    lineas.append("")

    if r["tablas_simbolos"]:
        lineas += ["## Tablas de símbolos", ""]
        for t in r["tablas_simbolos"]:
            lineas.append(f"### `{t['ruta']}` — {t['simbolos']} símbolos")
            lineas.append("")
            lineas.append("| Símbolo | Dirección | Tipo | Comentario |")
            lineas.append("| --- | --- | --- | --- |")
            for s in t["muestra"]:
                lineas.append(
                    f"| {s['nombre']} | {s['direccion'] or ''} | "
                    f"{s['tipo_dato'] or ''} | {s['comentario'] or ''} |"
                )
            lineas.append("")

    if r["listas_mensajes"]:
        lineas += ["## Listas de mensajes", ""]
        for m in r["listas_mensajes"]:
            lineas.append(f"### `{m['ruta']}` — {m['alarmas']} mensajes")
            lineas.append("")
            lineas.append("| Código | Texto | Clase |")
            lineas.append("| --- | --- | --- |")
            for a in m["muestra"]:
                lineas.append(f"| {a['codigo'] or ''} | {a['texto']} | {a['clase'] or ''} |")
            lineas.append("")

    for clave, titulo in (("bloques", "Bloques"), ("pantallas", "Pantallas")):
        if r[clave]:
            total = r[f"total_{clave}"]
            recorte = " (primeros)" if total > len(r[clave]) else ""
            lineas += [f"## {titulo}: {total}{recorte}", ""]
            lineas += [f"- `{x}`" for x in r[clave]]
            lineas.append("")

    return "\n".join(lineas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("origen", help="archivado .zip/.zap o carpeta ya extraída")
    parser.add_argument("--salida", help="fichero JSON donde guardar el detalle")
    parser.add_argument("--markdown", help="fichero .md donde guardar el resumen")
    parser.add_argument("--muestra", type=int, default=15,
                        help="filas de ejemplo por tabla (por defecto 15)")
    args = parser.parse_args(argv)

    try:
        resumen = radiografiar(args.origen, muestra=args.muestra)
    except (ValueError, FileNotFoundError) as error:
        print(error)
        return 1

    texto = a_markdown(resumen)
    print(texto)

    for ruta, contenido in (
        (args.salida, lambda: json.dumps(resumen, indent=2, ensure_ascii=False)),
        (args.markdown, lambda: texto),
    ):
        if ruta:
            destino = Path(ruta)
            destino.write_text(contenido(), encoding="utf-8")
            print(f"\nEscrito {destino} ({destino.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # Se ha canalizado la salida a `head`, `more` o similar.
        raise SystemExit(0)
