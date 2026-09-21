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

**Archivados en un recurso de red.** Cuando los proyectos viven en una carpeta
del cliente (`\\10.103.160.72\Proyectos\...`), este comando busca el archivado más
reciente, lo registra y opcionalmente lo descomprime e importa sus tablas de
símbolos:

```bash
# Solo mirar qué hay, sin tocar nada:
python -m guardias.archivar "\\10.103.160.72\Proyectos\Maval\C700\Dosificado\PLC"

# Registrar el más reciente y extraerlo:
python -m guardias.archivar "\\10.103.160.72\Proyectos\Maval\C700\Dosificado\PLC" \
    --planta C700 --extraer
```

Elige por la fecha del nombre del fichero — `20260918` (aaaammdd),
`11092026` (ddmmaaaa, la convención del C700), `21-09-2026` y `210926` — y solo
recurre a la fecha de modificación cuando el nombre no la
lleva: el mtime se altera al copiar entre unidades de red y engaña. Opciones:
`--nombre` para forzar un archivado concreto, `--copiar` para traerte una copia
local, `--crear-planta` para darla de alta al vuelo, `--destino` para elegir
dónde extraer.

Se extraen `.zip` y `.zap`; los `.7z`, `.rar` y los autoextraíbles hay que
abrirlos con su herramienta. Las rutas internas del archivo se validan antes de
escribir, así que una entrada con `../` no puede salirse de la carpeta destino.

**Archivos de proyecto** (`.zap`, `.zip`). Se guardan fuera del repositorio, en
`datos/adjuntos/proyectos/`, y en la base solo quedan la huella sha256, el
inventario de ficheros y la versión deducida. Subir dos veces la misma copia no
la duplica.

**Carpeta de un multiproyecto STEP7/PCS7.** Aunque el programa esté en binario,
la carpeta del multiproyecto trae dos ficheros legibles que son justo la ficha
de planta: `ApiLog/Step7Bas.ver` (inventario del software de la estación de
ingeniería con versiones y service packs) y `s7extref/s7envref.xml` (los
proyectos que cuelgan del multiproyecto, con el nombre de la ES y la ruta local
de cada `.s7p`). `importar_estacion()` los vuelca en la ficha de la planta.

Si una estación tiene instaladas dos versiones de la misma librería —la
heredada y la actual— se guardan las dos: saber que la vieja sigue ahí importa
durante una guardia.

## Compartir un proyecto sin mandar el proyecto

Un archivado de PCS7 son cientos de megas de binarios: no se puede adjuntar ni
leer de un vistazo. Este comando saca una **radiografía** — solo lo que es texto
y sirve para entender el programa — en unas decenas de KB:

```bash
python -m guardias.radiografia "D:\proyectos\Dosificado_C700_20260918.zap" \
    --salida ficha_C700.json --markdown ficha_C700.md
```

Devuelve estaciones, versión deducida, recuento por extensión, tablas de
símbolos con muestra de filas, listas de mensajes, y los bloques y pantallas que
contiene. Funciona igual sobre el `.zip`/`.zap` que sobre la carpeta ya
extraída. `--muestra N` ajusta cuántas filas de ejemplo lleva cada tabla.

Un `.txt` cualquiera del proyecto no se cuela como lista de mensajes: solo
cuenta como tal si la mayoría de sus filas traen código de mensaje.

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
| `guardias/importadores/` | Exportaciones de Siemens y carpeta del multiproyecto. |
| `guardias/archivar.py` | Localiza y extrae archivados desde la red del cliente. |
| `guardias/radiografia.py` | Resumen ligero de un proyecto, para compartir o consultar. |
| `guardias/templates/` | Plantillas Jinja2. |

Las marcas de tiempo se guardan en hora local (`datetime('now','localtime')`),
que es la que lees en el parte y la que teclea el navegador.
