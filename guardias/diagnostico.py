"""Orientación ante una alarma: por dónde puede venir.

Tres fuentes, de más a menos fiable:

1. Lo que ya sabes -- la alarma en tu base, con la causa y la actuación que
   escribiste tú y que ya comprobaste en campo.
2. Lo que ya te pasó -- avisos anteriores parecidos, con su solución.
3. Causas típicas -- el catálogo de abajo. Es conocimiento genérico de líneas
   de dosificado, NO de tu planta: sirve para no partir de cero a las tres de
   la mañana, y en cuanto confirmes una causa la pasas a tu base de alarmas,
   que es la que de verdad vale.
"""

from __future__ import annotations

import re
import sqlite3
import unicodedata

from . import consultas

# Cada pista son las causas habituales de una familia de fallo y qué mirar
# para descartarlas, en el orden en que compensa mirarlas.
PISTAS: tuple[dict, ...] = (
    {
        "id": "sobrecarga_motor",
        "titulo": "Sobrecarga o disparo térmico del motor",
        "claves": ("sobrecarga", "termico", "guardamotor", "overload", "uberlast",
                   "disparo", "magnetotermico", "sobreintensidad", "sobrecorriente"),
        "causas": [
            "Producto apelmazado o atascado en la tolva o en el sinfín: la humedad "
            "de la harina es la causa número uno en dosificado.",
            "Rodamiento o reductor agarrotado.",
            "Cuerpo extraño en el sinfín o en la esclusa.",
            "Relé térmico mal ajustado o degradado tras muchos arranques.",
            "Fallo de fase en la alimentación del motor.",
        ],
        "comprobaciones": [
            "Consumo del motor en vacío tras rearmar: si sigue alto, es mecánico.",
            "Nivel y estado del producto en la tolva; mira el vibrador o fluidificador.",
            "Histórico: si rearma y vuelve a disparar en minutos, no lo rearmes más.",
        ],
        "criticidad": "alta",
    },
    {
        "id": "variador",
        "titulo": "Fallo del variador",
        "claves": ("variador", "drive", "sinamics", "micromaster", "convertidor",
                   "inverter", "antriebs", "frecuencia"),
        "causas": [
            "Fallo propio del variador: sobreintensidad, sobretensión de bus por "
            "deceleración brusca, sobretemperatura del disipador.",
            "Filtro de ventilación del armario sucio: muy típico en fábrica de pan "
            "por el polvo de harina.",
            "Pérdida de comunicación Profibus/Profinet con el variador.",
            "Parámetros perdidos tras sustituir el equipo sin cargar el juego correcto.",
        ],
        "comprobaciones": [
            "Código de fallo en el display del variador: dice mucho más que la alarma del SCADA.",
            "Temperatura del armario y estado de los filtros.",
            "Si se sustituyó recientemente, confirma que se cargaron los parámetros.",
        ],
        "criticidad": "alta",
    },
    {
        "id": "bascula",
        "titulo": "Báscula fuera de tolerancia o peso incorrecto",
        "claves": ("bascula", "peso", "pesaje", "tolerancia", "siwarex", "celula",
                   "carga", "weight", "waage", "dosis", "dosificacion incorrecta"),
        "causas": [
            "Producto adherido en la tolva de pesaje: arrastra el cero poco a poco.",
            "Tara desajustada o deriva térmica de las células de carga.",
            "Vibración mecánica externa: un motor cercano o un golpe en la estructura.",
            "Célula de carga dañada o cable de señal con humedad.",
            "Caída en vuelo mal compensada tras cambiar de producto o de velocidad.",
            "Puente o tope mecánico tocando la tolva y falseando la lectura.",
        ],
        "comprobaciones": [
            "Mira el peso en vacío: si no es cero, es tara o suciedad.",
            "Prueba con pesa patrón si la hay.",
            "Compara las cuatro células si el SIWAREX lo permite: una descuadrada canta.",
            "¿Falla siempre con el mismo producto? Entonces es la compensación de vuelo.",
        ],
        "criticidad": "alta",
    },
    {
        "id": "nivel",
        "titulo": "Nivel de tolva o silo",
        "claves": ("nivel", "tolva", "silo", "minimo", "maximo", "vacio", "lleno",
                   "level", "fullstand", "rebose"),
        "causas": [
            "Falta de producto de verdad: mira antes de tocar nada.",
            "Sonda de nivel sucia o con producto adherido, que da nivel permanente.",
            "Bóveda de producto sobre la sonda: hay material, pero no baja.",
            "Vibrador o fluidificador de la tolva parado o mal temporizado.",
            "Sonda capacitiva desajustada tras cambio de producto.",
        ],
        "comprobaciones": [
            "Confirma con el operario el nivel real en planta, no el del SCADA.",
            "Golpea suavemente la tolva: si el nivel cae de golpe, era una bóveda.",
            "Estado del vibrador y su temporización.",
        ],
        "criticidad": "media",
    },
    {
        "id": "tiempo_dosificacion",
        "titulo": "Tiempo de dosificación excedido (timeout)",
        "claves": ("tiempo", "timeout", "excedido", "supervision", "vigilancia",
                   "zeit", "no alcanza", "no llega", "incompleto"),
        "causas": [
            "Caudal por debajo del esperado: sinfín desgastado, tolva casi vacía, "
            "producto apelmazado.",
            "Válvula o compuerta que no abre del todo.",
            "Tiempo de supervisión parametrizado demasiado justo para ese producto "
            "o esa receta.",
            "Báscula que no ve subir el peso aunque el producto esté cayendo.",
        ],
        "comprobaciones": [
            "¿Llegó algo de producto o nada? Si algo llegó, es caudal; si nada, es apertura.",
            "Compara con el tiempo que tardaba antes en la misma receta.",
            "Mira si coincide con un cambio de producto o de proveedor.",
        ],
        "criticidad": "media",
    },
    {
        "id": "valvula",
        "titulo": "Válvula o compuerta sin confirmación de posición",
        "claves": ("valvula", "compuerta", "posicion", "final de carrera", "detector",
                   "no confirma", "discrepancia", "ventil", "klappe", "actuador"),
        "causas": [
            "Final de carrera desajustado, sucio o flojo.",
            "Falta de aire comprimido o presión baja en la red.",
            "Electroválvula piloto quemada o con la bobina suelta.",
            "Producto endurecido en el asiento que impide cerrar del todo.",
            "Tiempo de confirmación demasiado corto en el bloque.",
        ],
        "comprobaciones": [
            "¿Falla al abrir o al cerrar? Acota mucho.",
            "Presión de la red de aire.",
            "Acciona manualmente y mira si el detector conmuta.",
        ],
        "criticidad": "media",
    },
    {
        "id": "comunicacion",
        "titulo": "Fallo de comunicación con periferia",
        "claves": ("comunicacion", "profibus", "profinet", "et200", "esclavo", "slave",
                   "bus", "red", "desconectado", "fallo modulo", "station failure",
                   "baugruppe", "dp", "perdida"),
        "causas": [
            "Conector o terminador de bus flojo: la vibración de la fábrica los suelta.",
            "Módulo de la ET200 averiado o mal insertado.",
            "Caída de la alimentación 24 V de un armario o de un segmento.",
            "Ruido eléctrico de variadores mal apantallados.",
            "Un solo esclavo tirando el segmento entero.",
        ],
        "comprobaciones": [
            "¿Cayó un esclavo o varios? Varios del mismo armario apuntan a alimentación.",
            "LED de diagnóstico de la ET200 y del maestro DP.",
            "Diagnóstico del hardware en la ES: te dice qué esclavo y qué módulo.",
            "Si es intermitente, sospecha de conector o apantallamiento antes que de módulo.",
        ],
        "criticidad": "alta",
    },
    {
        "id": "cpu",
        "titulo": "Fallo de CPU o de la estación de automatización",
        "claves": ("cpu", "as ", "automation station", "stop", "parada cpu",
                   "redundancia", "hsystem", "sincronizacion", "master", "reserve"),
        "causas": [
            "Paso a STOP por fallo de programa: error de acceso a área, división "
            "por cero, OB de error no programado.",
            "Pérdida de redundancia: una de las dos CPUs caída o cable de "
            "sincronización dañado.",
            "Fallo de alimentación o de batería/memoria.",
            "Sobrecarga de ciclo tras un cambio de programa.",
        ],
        "comprobaciones": [
            "Búfer de diagnóstico de la CPU: ahí está el motivo exacto y la hora.",
            "Si es redundancia, no toques nada hasta saber qué CPU es la máster.",
            "¿Coincide con una descarga reciente de programa?",
        ],
        "criticidad": "alta",
    },
    {
        "id": "temperatura_agua",
        "titulo": "Temperatura del agua de proceso fuera de rango",
        "claves": ("temperatura", "agua", "frio", "calor", "refrigeracion", "grados",
                   "temperatur", "wasser", "enfriador", "chiller"),
        "causas": [
            "Grupo de frío parado o en fallo.",
            "Válvula mezcladora agarrotada o con el actuador suelto.",
            "Sonda de temperatura desviada o mal colocada.",
            "Consumo alto puntual: varias amasadas seguidas agotan el depósito.",
        ],
        "comprobaciones": [
            "Compara la sonda del SCADA con un termómetro en el punto de uso.",
            "Estado del grupo de frío y su consigna.",
            "¿Falla solo en horas punta de producción? Entonces es capacidad, no avería.",
        ],
        "criticidad": "media",
    },
    {
        "id": "senal_analogica",
        "titulo": "Señal analógica fuera de rango o rotura de hilo",
        "claves": ("analogica", "fuera de rango", "rotura de hilo", "drahtbruch",
                   "wire break", "4-20", "sonda", "sensor", "transmisor", "overflow",
                   "underflow", "invalid"),
        "causas": [
            "Rotura o mal contacto en el lazo 4-20 mA.",
            "Transmisor sin alimentación.",
            "Escalado mal configurado tras sustituir el sensor por otro rango.",
            "Humedad en la caja de conexiones: muy típico en zona de lavado.",
        ],
        "comprobaciones": [
            "Mide el lazo: 0 mA es rotura, 4 mA es cero real.",
            "Valor bruto en el módulo de entrada frente al escalado del bloque.",
            "¿Se cambió el sensor hace poco? Compara rangos.",
        ],
        "criticidad": "media",
    },
    {
        "id": "seguridad",
        "titulo": "Parada de emergencia o enclavamiento de seguridad",
        "claves": ("emergencia", "seta", "seguridad", "enclavamiento", "puerta",
                   "barrera", "not-aus", "emergency", "rearme", "guarda"),
        "causas": [
            "Seta pulsada o sin rearmar en algún punto de la línea.",
            "Puerta o guarda de protección abierta.",
            "Relé de seguridad en fallo o cableado de la cadena interrumpido.",
        ],
        "comprobaciones": [
            "Recorre la cadena: suele ser una seta olvidada en un punto alejado.",
            "Nunca puentees ni anules un enclavamiento: esto es seguridad de personas.",
            "El rearme se hace en planta, con vista sobre la máquina.",
        ],
        "criticidad": "alta",
    },
    {
        "id": "receta_batch",
        "titulo": "Receta o lote que no arranca (SIMATIC BATCH)",
        "claves": ("receta", "batch", "lote", "charge", "rezept", "formula",
                   "no arranca", "secuencia", "sfc", "unidad ocupada"),
        "causas": [
            "Unidad ocupada por un lote anterior mal cerrado.",
            "Condición de arranque no cumplida: una válvula, un nivel, un permiso.",
            "Receta modificada y no liberada.",
            "Equipo en manual o fuera de servicio desde el SCADA.",
        ],
        "comprobaciones": [
            "Mira el SFC paso a paso: te dice en qué transición se queda.",
            "Estado de ocupación de las unidades implicadas.",
            "¿Alguien dejó algo en manual en el turno anterior?",
        ],
        "criticidad": "media",
    },
)


def _palabras(texto: str) -> str:
    """Texto en minúsculas, sin acentos y rodeado de espacios.

    Se conservan los separadores de palabra a propósito: comparando sobre el
    texto sin espacios, "carga" encaja dentro de "sobrecarga" y "as" dentro de
    "bascula", y el diagnóstico empieza a proponer cosas que no vienen a cuento.
    """
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFD", texto or "")
        if unicodedata.category(c) != "Mn"
    )
    return " " + re.sub(r"[^a-z0-9]+", " ", sin_acentos.lower()).strip() + " "


def buscar_pistas(texto: str, *, limite: int = 3) -> list[dict]:
    """Pistas del catálogo que encajan con el texto de la alarma.

    Se puntúa por número de claves distintas encontradas, así que una alarma
    que mencione a la vez la báscula y la tolerancia pesa más que otra que
    solo diga «peso».
    """
    consulta = _palabras(texto)
    if not consulta.strip():
        return []

    puntuadas = []
    for pista in PISTAS:
        aciertos = {c for c in pista["claves"] if _palabras(c).strip() and
                    _palabras(c) in consulta}
        if aciertos:
            puntuadas.append((len(aciertos), pista))

    puntuadas.sort(key=lambda p: p[0], reverse=True)
    return [pista for _, pista in puntuadas[:limite]]


def diagnosticar(con: sqlite3.Connection, texto: str, *, planta_id: int | None = None) -> dict:
    """Reúne lo que se sabe de una alarma: tu base, tu histórico y el catálogo."""
    if not texto.strip():
        return {"texto": texto, "alarmas": [], "incidencias": [], "pistas": [], "simbolos": []}

    encontradas = consultas.buscar(con, texto, entidad="alarma", limite=8, flexible=True)
    ids = [f["entidad_id"] for f in encontradas]
    alarmas = []
    if ids:
        marcas = ", ".join("?" * len(ids))
        alarmas = consultas.todos(
            con,
            "SELECT a.*, p.codigo AS planta_codigo FROM alarma a"
            " LEFT JOIN planta p ON p.id = a.planta_id"
            f" WHERE a.id IN ({marcas})",
            ids,
        )
        orden = {id_: n for n, id_ in enumerate(ids)}
        alarmas.sort(key=lambda a: orden.get(a["id"], 99))

    return {
        "texto": texto,
        "alarmas": alarmas,
        "incidencias": consultas.buscar(
            con, texto, entidad="incidencia", limite=8, planta_id=planta_id, flexible=True
        ),
        "pistas": buscar_pistas(texto),
        "simbolos": consultas.buscar_simbolos(con, texto, limite=10),
    }
