"""Interfaz web local de la herramienta de guardia."""

from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from . import __version__, consultas
from .db import abrir, actualizar, borrar, insertar, ruta_adjuntos, todos, uno
from .importadores import importar_alarmas, importar_proyecto, importar_simbolos
from .importadores.estacion import importar_estacion

BASE = Path(__file__).resolve().parent
plantillas = Jinja2Templates(directory=str(BASE / "templates"))

# Centinelas con los que la búsqueda marca las coincidencias (ver consultas.buscar).
MARCA_INICIO, MARCA_FIN = "\x02", "\x03"


def resaltar(texto: str | None) -> Markup:
    """Escapa el extracto y solo después convierte las marcas en <mark>."""
    seguro = str(escape(texto or ""))
    return Markup(seguro.replace(MARCA_INICIO, "<mark>").replace(MARCA_FIN, "</mark>"))


plantillas.env.filters["resaltar"] = resaltar

# Tablas cuyo borrado se permite desde la interfaz.
BORRABLES = {"contacto", "equipo", "software", "alarma", "incidencia", "planta", "proyecto", "guardia"}

CAMPOS_PLANTA = (
    "codigo", "nombre", "localidad", "provincia", "cliente", "tipo_linea",
    "criticidad", "horario", "acceso_remoto", "direccion", "notas",
)
CAMPOS_INCIDENCIA = (
    "planta_id", "guardia_id", "equipo_id", "alarma_id", "titulo", "recibido",
    "cerrado", "canal", "avisado_por", "area", "sintoma", "diagnostico",
    "solucion", "parada_min", "resuelto_remoto", "estado", "criticidad",
    "acciones", "etiquetas",
)
CAMPOS_ALARMA = (
    "planta_id", "codigo", "texto", "clase", "area", "equipo_id", "causa",
    "actuacion", "criticidad", "requiere_parada", "referencias", "verificada",
)
ENTEROS = {
    "planta_id", "guardia_id", "equipo_id", "alarma_id", "parada_min",
    "resuelto_remoto", "requiere_parada", "verificada", "repuesto", "prioridad",
}
# Campos de fecha/hora: el navegador los manda como 2026-09-21T08:00.
FECHAS = {"recibido", "cerrado", "inicio", "fin", "fecha_version"}


def normalizar_fecha(valor: str) -> str:
    """Pasa el formato del navegador al que usa SQLite (espacio y segundos)."""
    valor = valor.replace("T", " ", 1)
    if len(valor) == 16:  # falta el campo de segundos
        valor += ":00"
    return valor


def ahora() -> str:
    """Marca de tiempo local, igual que datetime('now','localtime') en SQLite."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def limpiar(datos: dict[str, Any], campos: tuple[str, ...] | None = None) -> dict[str, Any]:
    """Normaliza un formulario: vacíos a None y numéricos a entero."""
    salida: dict[str, Any] = {}
    for clave, valor in datos.items():
        if campos and clave not in campos:
            continue
        if isinstance(valor, str):
            valor = valor.strip()
            if valor == "":
                salida[clave] = None
                continue
            if clave in ENTEROS:
                try:
                    valor = int(valor)
                except ValueError:
                    valor = None
            elif clave in FECHAS:
                valor = normalizar_fecha(valor)
        salida[clave] = valor
    return salida


def casillas(datos: dict[str, Any], nombres: tuple[str, ...]) -> dict[str, Any]:
    """Las casillas sin marcar no se envían: se fuerzan a 0."""
    for n in nombres:
        datos[n] = 1 if datos.get(n) else 0
    return datos


def crear_app(ruta_bd: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Guardia dosificado", version=__version__)
    con: sqlite3.Connection = abrir(ruta_bd)
    app.state.con = con

    estaticos = BASE / "static"
    estaticos.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(estaticos)), name="static")

    def render(peticion: Request, plantilla: str, **ctx: Any) -> HTMLResponse:
        ctx.setdefault("plantas", todos(con, "SELECT id, codigo, nombre FROM planta ORDER BY codigo"))
        ctx.setdefault("version", __version__)
        return plantillas.TemplateResponse(peticion, plantilla, ctx)

    def volver(destino: str) -> RedirectResponse:
        return RedirectResponse(destino, status_code=303)

    async def formulario(peticion: Request) -> dict[str, Any]:
        return {k: v for k, v in (await peticion.form()).multi_items()}

    # ------------------------------------------------------------- panel

    @app.get("/", response_class=HTMLResponse)
    def panel(peticion: Request):
        return render(
            peticion,
            "panel.html",
            resumen=consultas.resumen(con),
            activa=consultas.guardia_activa(con),
            proxima=consultas.proxima_guardia(con),
            abiertas=consultas.incidencias_abiertas(con),
            actividad=consultas.actividad_por_planta(con),
        )

    @app.get("/buscar", response_class=HTMLResponse)
    def buscar(peticion: Request, q: str = ""):
        return render(
            peticion,
            "buscar.html",
            q=q,
            resultados=consultas.buscar(con, q) if q else [],
            simbolos=consultas.buscar_simbolos(con, q, limite=30) if q else [],
        )

    @app.get("/api/buscar")
    def api_buscar(q: str = "", entidad: str | None = None):
        filas = consultas.buscar(con, q, entidad=entidad) if q else []
        return [dict(f) for f in filas]

    # ------------------------------------------------------------ plantas

    @app.get("/plantas", response_class=HTMLResponse)
    def lista_plantas(peticion: Request):
        return render(
            peticion,
            "plantas.html",
            filas=todos(
                con,
                "SELECT p.*, (SELECT count(*) FROM incidencia i WHERE i.planta_id = p.id"
                "   AND i.estado != 'cerrada') AS abiertas,"
                " (SELECT count(*) FROM alarma a WHERE a.planta_id = p.id) AS n_alarmas"
                " FROM planta p ORDER BY p.codigo",
            ),
        )

    @app.post("/plantas")
    async def crear_planta(peticion: Request):
        datos = limpiar(await formulario(peticion), CAMPOS_PLANTA)
        planta_id = insertar(con, "planta", datos)
        return volver(f"/plantas/{planta_id}")

    @app.get("/plantas/{planta_id}", response_class=HTMLResponse)
    def ver_planta(peticion: Request, planta_id: int, mensaje: str = ""):
        ficha = consultas.ficha_planta(con, planta_id)
        if ficha is None:
            return volver("/plantas")
        return render(peticion, "planta.html", mensaje=mensaje, **ficha)

    @app.post("/plantas/{planta_id}")
    async def editar_planta(peticion: Request, planta_id: int):
        actualizar(con, "planta", planta_id, limpiar(await formulario(peticion), CAMPOS_PLANTA))
        return volver(f"/plantas/{planta_id}")

    @app.post("/plantas/{planta_id}/contactos")
    async def crear_contacto(peticion: Request, planta_id: int):
        datos = limpiar(await formulario(peticion))
        datos["planta_id"] = planta_id
        insertar(con, "contacto", datos)
        return volver(f"/plantas/{planta_id}#contactos")

    @app.post("/plantas/{planta_id}/equipos")
    async def crear_equipo(peticion: Request, planta_id: int):
        datos = casillas(limpiar(await formulario(peticion)), ("repuesto",))
        datos["planta_id"] = planta_id
        insertar(con, "equipo", datos)
        return volver(f"/plantas/{planta_id}#equipos")

    @app.post("/plantas/{planta_id}/software")
    async def crear_software(peticion: Request, planta_id: int):
        datos = limpiar(await formulario(peticion))
        datos["planta_id"] = planta_id
        insertar(con, "software", datos)
        return volver(f"/plantas/{planta_id}#software")

    @app.post("/borrar/{tabla}/{id_}")
    def borrar_fila(tabla: str, id_: int, destino: str = Form("/")):
        if tabla in BORRABLES:
            borrar(con, tabla, id_)
        return volver(destino)

    # -------------------------------------------------------- incidencias

    @app.get("/incidencias", response_class=HTMLResponse)
    def lista_incidencias(peticion: Request, planta_id: int | None = None, estado: str | None = None):
        return render(
            peticion,
            "incidencias.html",
            filas=consultas.listar_incidencias(con, planta_id=planta_id, estado=estado),
            planta_id=planta_id,
            estado=estado,
        )

    @app.get("/incidencias/nueva", response_class=HTMLResponse)
    def nueva_incidencia(peticion: Request, planta_id: int | None = None, alarma_id: int | None = None):
        return render(
            peticion,
            "incidencia_nueva.html",
            planta_id=planta_id,
            alarma=uno(con, "SELECT * FROM alarma WHERE id = ?", (alarma_id,)) if alarma_id else None,
            guardia=consultas.guardia_activa(con),
        )

    @app.post("/incidencias")
    async def crear_incidencia(peticion: Request):
        datos = casillas(
            limpiar(await formulario(peticion), CAMPOS_INCIDENCIA), ("resuelto_remoto",)
        )
        activa = consultas.guardia_activa(con)
        if activa is not None and not datos.get("guardia_id"):
            datos["guardia_id"] = activa["id"]
        return volver(f"/incidencias/{insertar(con, 'incidencia', datos)}")

    @app.get("/incidencias/{incidencia_id}", response_class=HTMLResponse)
    def ver_incidencia(peticion: Request, incidencia_id: int):
        fila = uno(con, "SELECT * FROM incidencia WHERE id = ?", (incidencia_id,))
        if fila is None:
            return volver("/incidencias")
        return render(
            peticion,
            "incidencia.html",
            i=fila,
            planta=uno(con, "SELECT * FROM planta WHERE id = ?", (fila["planta_id"],)),
            equipos=todos(con, "SELECT * FROM equipo WHERE planta_id = ? ORDER BY nombre", (fila["planta_id"],)),
            parecidas=consultas.reincidencias(con, fila),
        )

    @app.post("/incidencias/{incidencia_id}")
    async def editar_incidencia(peticion: Request, incidencia_id: int):
        datos = casillas(
            limpiar(await formulario(peticion), CAMPOS_INCIDENCIA), ("resuelto_remoto",)
        )
        if datos.get("estado") == "cerrada" and not datos.get("cerrado"):
            # Al cerrar sin fecha explícita se sella con la hora actual.
            anterior = uno(con, "SELECT cerrado FROM incidencia WHERE id = ?", (incidencia_id,))
            datos["cerrado"] = (anterior["cerrado"] if anterior else None) or ahora()
        actualizar(con, "incidencia", incidencia_id, datos)
        return volver(f"/incidencias/{incidencia_id}")

    # ------------------------------------------------------------ alarmas

    @app.get("/alarmas", response_class=HTMLResponse)
    def lista_alarmas(peticion: Request, q: str = "", planta_id: int | None = None):
        if q:
            encontradas = consultas.buscar(con, q, entidad="alarma", limite=100)
            ids = [f["entidad_id"] for f in encontradas]
            filas = (
                todos(
                    con,
                    "SELECT a.*, p.codigo AS planta_codigo FROM alarma a"
                    " LEFT JOIN planta p ON p.id = a.planta_id"
                    f" WHERE a.id IN ({', '.join('?' * len(ids))})",
                    ids,
                )
                if ids
                else []
            )
            orden = {id_: n for n, id_ in enumerate(ids)}
            filas.sort(key=lambda f: orden.get(f["id"], 999))
        else:
            sql = (
                "SELECT a.*, p.codigo AS planta_codigo FROM alarma a"
                " LEFT JOIN planta p ON p.id = a.planta_id"
            )
            params: list[Any] = []
            if planta_id:
                sql += " WHERE a.planta_id = ?"
                params.append(planta_id)
            sql += " ORDER BY a.planta_id, a.codigo LIMIT 300"
            filas = todos(con, sql, params)
        return render(peticion, "alarmas.html", filas=filas, q=q, planta_id=planta_id)

    @app.post("/alarmas")
    async def crear_alarma(peticion: Request):
        datos = casillas(
            limpiar(await formulario(peticion), CAMPOS_ALARMA),
            ("requiere_parada", "verificada"),
        )
        return volver(f"/alarmas/{insertar(con, 'alarma', datos)}")

    @app.get("/alarmas/{alarma_id}", response_class=HTMLResponse)
    def ver_alarma(peticion: Request, alarma_id: int):
        fila = uno(con, "SELECT * FROM alarma WHERE id = ?", (alarma_id,))
        if fila is None:
            return volver("/alarmas")
        return render(
            peticion,
            "alarma.html",
            a=fila,
            historico=todos(
                con,
                "SELECT i.*, p.codigo AS planta_codigo FROM incidencia i"
                " JOIN planta p ON p.id = i.planta_id"
                " WHERE i.alarma_id = ? ORDER BY i.recibido DESC LIMIT 20",
                (alarma_id,),
            ),
        )

    @app.post("/alarmas/{alarma_id}")
    async def editar_alarma(peticion: Request, alarma_id: int):
        datos = casillas(
            limpiar(await formulario(peticion), CAMPOS_ALARMA),
            ("requiere_parada", "verificada"),
        )
        actualizar(con, "alarma", alarma_id, datos)
        return volver(f"/alarmas/{alarma_id}")

    # ----------------------------------------------------------- guardias

    @app.get("/guardias", response_class=HTMLResponse)
    def lista_guardias(peticion: Request):
        return render(
            peticion,
            "guardias.html",
            filas=todos(
                con,
                "SELECT g.*, (SELECT count(*) FROM incidencia i WHERE i.guardia_id = g.id)"
                " AS avisos FROM guardia g ORDER BY g.inicio DESC LIMIT 100",
            ),
            activa=consultas.guardia_activa(con),
        )

    @app.post("/guardias")
    async def crear_guardia(peticion: Request):
        insertar(con, "guardia", limpiar(await formulario(peticion)))
        return volver("/guardias")

    # ---------------------------------------------------------- proyectos

    @app.get("/proyectos/{proyecto_id}", response_class=HTMLResponse)
    def ver_proyecto(peticion: Request, proyecto_id: int, q: str = ""):
        fila = uno(con, "SELECT * FROM proyecto WHERE id = ?", (proyecto_id,))
        if fila is None:
            return volver("/plantas")
        return render(
            peticion,
            "proyecto.html",
            p=fila,
            planta=uno(con, "SELECT * FROM planta WHERE id = ?", (fila["planta_id"],)),
            q=q,
            simbolos=consultas.buscar_simbolos(con, q, proyecto_id=proyecto_id)
            if q
            else todos(
                con,
                "SELECT s.*, '' AS proyecto FROM simbolo s WHERE proyecto_id = ?"
                " ORDER BY nombre LIMIT 100",
                (proyecto_id,),
            ),
            entradas=todos(
                con,
                "SELECT * FROM proyecto_entrada WHERE proyecto_id = ? ORDER BY ruta LIMIT 500",
                (proyecto_id,),
            ),
        )

    # ---------------------------------------------------------- importar

    @app.get("/importar", response_class=HTMLResponse)
    def form_importar(peticion: Request, mensaje: str = ""):
        return render(
            peticion,
            "importar.html",
            mensaje=mensaje,
            proyectos=todos(
                con,
                "SELECT pr.id, pr.nombre, p.codigo FROM proyecto pr"
                " JOIN planta p ON p.id = pr.planta_id ORDER BY p.codigo, pr.nombre",
            ),
        )

    @app.post("/importar/alarmas")
    async def subir_alarmas(fichero: UploadFile, planta_id: int | None = Form(None)):
        r = importar_alarmas(con, await fichero.read(), planta_id=planta_id)
        return volver(
            f"/importar?mensaje=Alarmas: {r['nuevas']} nuevas, {r['actualizadas']} actualizadas"
            f" de {r['leidas']} leídas."
        )

    @app.post("/importar/simbolos")
    async def subir_simbolos(fichero: UploadFile, proyecto_id: int = Form(...)):
        r = importar_simbolos(con, proyecto_id, await fichero.read())
        return volver(f"/importar?mensaje=Símbolos importados: {r['importados']}.")

    @app.post("/importar/estacion")
    async def subir_estacion(fichero: UploadFile, planta_id: int = Form(...),
                             todo: str = Form("")):
        """Carpeta del multiproyecto comprimida: rellena el software de la ficha."""
        import tempfile

        from .archivar import extraer

        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / Path(fichero.filename or "multiproyecto.zip").name
            with copia.open("wb") as salida:
                shutil.copyfileobj(fichero.file, salida)
            try:
                carpeta = extraer(copia, Path(tmp) / "extraido")
            except ValueError as error:
                return volver(f"/importar?mensaje=No se ha podido abrir: {error}")
            r = importar_estacion(con, planta_id, carpeta, todo=bool(todo))

        aviso = " El multiproyecto viene sin el programa (no hay ningún .s7p)." if r["vacio"] else ""
        estacion = f" Estación: {r['estacion_ingenieria']}." if r["estacion_ingenieria"] else ""
        proyectos = ", ".join(p["nombre"] for p in r["proyectos"])
        return volver(
            f"/plantas/{planta_id}?mensaje=Software: {r['nuevos']} productos nuevos"
            f" de {r['guardados']}.{estacion}"
            f"{' Proyectos: ' + proyectos + '.' if proyectos else ''}{aviso}"
        )

    @app.post("/importar/proyecto")
    async def subir_proyecto(
        fichero: UploadFile,
        planta_id: int = Form(...),
        nombre: str = Form(""),
        origen: str = Form(""),
    ):
        destino_dir = ruta_adjuntos() / "proyectos" / str(planta_id)
        destino_dir.mkdir(parents=True, exist_ok=True)
        destino = destino_dir / Path(fichero.filename or "proyecto.zip").name
        with destino.open("wb") as salida:
            shutil.copyfileobj(fichero.file, salida)
        r = importar_proyecto(
            con, planta_id, destino, nombre=nombre or None, origen=origen or None
        )
        return volver(f"/proyectos/{r['proyecto_id']}")

    return app


app = crear_app()
