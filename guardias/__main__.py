"""Arranque del servidor local: ``python -m guardias``."""

from __future__ import annotations

import argparse
import webbrowser

import uvicorn

from .db import ruta_bd


def main() -> None:
    parser = argparse.ArgumentParser(description="Herramienta de guardia de dosificado")
    parser.add_argument("--host", default="127.0.0.1", help="por defecto solo local")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--abrir", action="store_true", help="abre el navegador al arrancar")
    parser.add_argument("--recargar", action="store_true", help="recarga al editar (desarrollo)")
    args = parser.parse_args()

    print(f"Base de datos: {ruta_bd()}")
    print(f"Interfaz:      http://{args.host}:{args.puerto}")
    if args.abrir:
        webbrowser.open(f"http://{args.host}:{args.puerto}")

    uvicorn.run(
        "guardias.web:app", host=args.host, port=args.puerto, reload=args.recargar
    )


if __name__ == "__main__":
    main()
