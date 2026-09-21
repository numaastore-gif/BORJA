# Guardia · Dosificado (Mercadona)

Herramienta local para dar soporte de guardia a las líneas de dosificado de las
fábricas de pan: ficha técnica de cada planta, registro de avisos y base de
conocimiento de alarmas de PCS7 / WinCC, todo buscable por el texto que el
operario te dicta por teléfono.

Funciona en tu portátil, contra un fichero SQLite. No necesita internet ni
acceso a la red del cliente.

## Puesta en marcha

```bash
pip install -r requirements.txt
python -m guardias.ejemplo      # opcional: carga una planta de muestra
python -m guardias --abrir      # http://127.0.0.1:8000
```

Opciones útiles: `--puerto 8080`, `--recargar` (desarrollo), `--host 0.0.0.0`
(solo si de verdad quieres exponerlo en la red; **no tiene autenticación**).

## Qué hay dentro

| Sección | Para qué sirve |
| --- | --- |
| **Panel** | Quién está de guardia, avisos abiertos y qué planta te está consumiendo el tiempo. |
| **Plantas** | Ficha técnica: hardware (AS, OS, ET200, básculas), versiones de PCS7/WinCC, IPs, cómo se entra en remoto y a quién se llama. |
| **Incidencias** | Histórico de avisos: síntoma, diagnóstico, solución, minutos de parada. Al abrir uno te muestra los parecidos anteriores de esa misma planta. |
| **Alarmas** | Base de conocimiento: texto de la alarma → causa probable y actuación paso a paso. |
| **Guardias** | Calendario de turnos. Los avisos se asignan solos al turno en curso. |
| **Importar** | Carga de exportaciones de PCS7/WinCC (abajo). |

La búsqueda de la barra superior va contra alarmas, incidencias y variables del
programa a la vez, ignora acentos y tolera que pegues el texto con comillas y
guiones tal cual sale del SCADA.

## Importar desde PCS7 / WinCC

**Listas de alarmas** (`.csv`, `.txt`, `.sdf`). Se reconocen las cabeceras en
alemán, inglés y español (`Nummer`/`Number`/`Número`, `Meldetext`/`Message
text`/`Texto`…) y las codificaciones que suelta una estación de ingeniería
(UTF-8, UTF-16, CP1252). Al reimportar una versión nueva se refrescan el texto y
la clase, pero **nunca** se pisan la causa ni la actuación que hayas escrito tú:
ese es el valor que vas acumulando.

**Tablas de símbolos de STEP7** (`.asc` de ancho fijo, `.sdf`, `.csv`, `.txt`).
Quedan asociadas a un proyecto y buscables por símbolo, dirección o comentario,
que es lo que necesitas cuando te preguntan por una variable concreta a las 3 de
la mañana. Subir una versión nueva reemplaza la tabla anterior del proyecto.

**Archivos de proyecto** (`.zap`, `.zip`). Se guardan fuera del repositorio, en
`datos/adjuntos/proyectos/`, y en la base solo quedan la huella sha256, el
inventario de ficheros y la versión deducida. Subir dos veces la misma copia no
la duplica.

## Dónde viven los datos

| Qué | Dónde | Variable de entorno |
| --- | --- | --- |
| Base de datos | `datos/guardias.db` | `GUARDIAS_BD` |
| Adjuntos y proyectos | `datos/adjuntos/` | `GUARDIAS_ADJUNTOS` |

`datos/` está en `.gitignore` junto con `*.zap*`, `*.s7p` y `*.zip`: los
programas del cliente no deben acabar en el repositorio. Haz copia de seguridad
de esa carpeta por tu cuenta — es todo el histórico de guardias.

## Desarrollo

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q
```

| Fichero | Contenido |
| --- | --- |
| `guardias/schema.sql` | Esquema y disparadores del índice de búsqueda FTS5. |
| `guardias/db.py` | Conexión y utilidades de escritura. |
| `guardias/consultas.py` | Consultas del dominio (panel, fichas, búsqueda). |
| `guardias/web.py` | Rutas de la interfaz. |
| `guardias/importadores/` | Lectura de exportaciones de Siemens. |
| `guardias/templates/` | Plantillas Jinja2. |

Las marcas de tiempo se guardan en hora local (`datetime('now','localtime')`),
que es la que lees en el parte y la que teclea el navegador.
