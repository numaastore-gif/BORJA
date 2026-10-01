"""Traducción orientativa alemán -> español de los comentarios del programa.

No es una traducción completa: sustituye términos técnicos frecuentes de los
programas Langhammer para que el comentario se pueda leer de un vistazo. El
texto original se conserva siempre en la columna "Descripción programa".
"""
import re

GLOSARIO = [
    # frases primero
    ('MELDUNG MOTORSCHUTZ', 'aviso guardamotor'),
    ('MELDUNG NOT-AUS', 'aviso parada de emergencia'),
    ('MELDUNG SICHERH.-LS', 'aviso barrera de seguridad'),
    ('LEUCHTMELDER', 'piloto'),
    ('SICHERHEITSLICHTSCHRANKE', 'barrera fotoeléctrica de seguridad'),
    ('SICHERH.-LS', 'barrera de seguridad'),
    ('LICHTSCHRANKE', 'fotocélula'),
    ('LICHTTASTER', 'fotocélula de detección directa'),
    ('INITIATOR', 'detector inductivo'),
    ('NOT-AUS', 'parada de emergencia'),
    ('NOT-HALT', 'parada de emergencia'),
    ('MOTORSCHUTZ', 'guardamotor'),
    ('HAUPTVENTIL', 'válvula principal'),
    ('HAUPTSCHALTER', 'interruptor general'),
    ('WAHLSCHALTER', 'selector'),
    ('SCHUTZTÜR', 'puerta de protección'),
    ('TUER', 'puerta'), ('TÜR', 'puerta'),
    ('TASTER', 'pulsador'), ('TASTE', 'pulsador'),
    ('ANTRIEB', 'accionamiento'), ('ANTR.', 'accionamiento'),
    ('VENTIL', 'electroválvula'),
    ('ZYLINDER', 'cilindro'),
    ('KLEMMER', 'pinza'), ('ZANGE', 'pinza'),
    ('ABSCHIEBER', 'empujador'),
    ('SAUGER', 'ventosa'),
    ('HUPE', 'bocina'), ('HORN', 'bocina'),
    ('SIGNALSAEULE', 'columna de señalización'),
    ('KARTONAUFRICHTER', 'formadora de cajas'),
    ('KARTONVERSCHLIESSER', 'cerradora de cajas'),
    ('KISTENBEDRUCKER', 'impresora de cajas'), ('KISTENDRUCKER', 'impresora de cajas'),
    ('ETIKETTIERER', 'etiquetadora'),
    ('PALETTIERER', 'paletizador'),
    ('PALETTENTRANSPORT', 'transporte de palets'),
    ('PALETTENHEBER', 'elevador de palets'),
    ('VOLLPALETTE', 'palet lleno'), ('LEERPALETTEN', 'palets vacíos'), ('LEERPALETTE', 'palet vacío'),
    ('HALBPALETTE', 'medio palet'), ('RESTEPALETTE', 'palet de restos'),
    ('PALETTE', 'palet'),
    ('LEERKARTON', 'caja vacía'), ('VOLLKARTONS', 'cajas llenas'), ('KARTON', 'caja'),
    ('KARTONTRANSPORT', 'transporte de cajas'),
    ('FALLSCHACHT', 'caída vertical'),
    ('ROLLENBAHN', 'transportador de rodillos'), ('ROLLBAHN', 'transportador de rodillos'),
    ('KETTE', 'cadena'),
    ('HUBWERK', 'mecanismo de elevación'), ('HUB AUF', 'elevación sube'), ('HUB AB', 'elevación baja'),
    ('HUB', 'elevación'),
    ('WAAGE', 'báscula'), ('GEWICHTSFEHLER', 'error de peso'), ('GEWICHT', 'peso'),
    ('QUERVERBINDUNG', 'conexión transversal'), ('QUERVERB.', 'conexión transversal'),
    ('STÖRUNG', 'avería'), ('STOERUNG', 'avería'), ('SAMMELSTÖRUNG', 'avería general'),
    ('SAMMELSTOERUNG', 'avería general'),
    ('LAUFZEITFEHLER', 'error de tiempo de recorrido'), ('ENDLAGENFEHLER', 'error de final de carrera'),
    ('FEHLER', 'error'),
    ('ÜBERWACHUNGSZEIT', 'tiempo de vigilancia'), ('VERZÖGERUNGSZEIT', 'tiempo de retardo'),
    ('VERZÖGERUNG', 'retardo'), ('VERZOEGERT', 'retardado'),
    ('FLANKENAUSWERTUNG', 'evaluación de flanco'), ('FLANKENMERKER', 'marca de flanco'),
    ('MERKER', 'marca'),
    ('ZUSTAND', 'estado'), ('ALTER', 'anterior'),
    ('BELEGT', 'ocupado'), ('FREIGABE', 'habilitación'), ('FRG', 'habilitación'),
    ('SPERRE', 'bloqueo'), ('GESPERRT', 'bloqueado'),
    ('BETRIEB', 'servicio'), ('AUTOMATIK', 'automático'), ('HANDBETRIEB', 'modo manual'), ('HAND', 'manual'),
    ('QUITTIERUNG', 'rearme'), ('QUITT', 'rearme'),
    ('ÜBERGABE', 'transferencia'), ('UEBERGABE', 'transferencia'), ('ÜBERNOMMEN', 'recibido'),
    ('EINLAUF', 'entrada'), ('AUSLAUF', 'salida'),
    ('OBEN', 'arriba'), ('UNTEN', 'abajo'), ('VORNE', 'delante'), ('VORN', 'delante'),
    ('HINTEN', 'detrás'), ('LINKS', 'izquierda'), ('RECHTS', 'derecha'),
    ('ZURUECK', 'atrás'), ('ZURÜCK', 'atrás'), ('VOR', 'adelante'),
    ('ENDLAGE', 'final de carrera'), ('POSITION', 'posición'),
    ('LINIE', 'línea'), ('SPUR', 'carril'), ('PLATZ', 'puesto'), ('STELLE', 'puesto'),
    ('ANLAGE', 'instalación'), ('ANFORDERUNG', 'petición'), ('BEFEHL', 'orden'),
    ('MAGAZIN', 'almacén'), ('KLEBEBANDMANGEL', 'falta de cinta adhesiva'), ('KLEBEBANDENDE', 'fin de cinta adhesiva'),
    ('DREHWÄCHTER', 'controlador de giro'), ('KALTLEITER', 'termistor PTC'),
    ('TEMPERATURÜBERWACHUNG', 'vigilancia de temperatura'),
    ('SEILSCHLAFF', 'cable flojo'), ('SCHLAFF', 'flojo'),
    ('PROFIBUSFEHLER', 'fallo Profibus'), ('KANALFEHLER', 'fallo de canal'),
    ('RESERVE', 'reserva'), ('MELDUNG', 'aviso'), ('LAMPE', 'lámpara'),
    ('AUF', 'sube'), ('AB', 'baja'), ('EIN', 'conectado'), ('AUS', 'desconectado'),
    ('NICHT', 'no'), ('UND', 'y'), ('MIT', 'con'), ('OHNE', 'sin'), ('FÜR', 'para'), ('VON', 'de'),
    ('NACH', 'hacia'), ('ZUM', 'al'), ('BEIM', 'en'), ('LEER', 'vacío'), ('VOLL', 'lleno'),
    ('BEREIT', 'listo'), ('AKTIV', 'activo'), ('BETÄTIGT', 'accionado'), ('GEÖFFNET', 'abierto'),
]

_PATRONES = [(re.compile(r'(?<![A-ZÄÖÜa-zäöüß])' + re.escape(de) + r'(?![A-ZÄÖÜa-zäöüß])', re.I), es)
             for de, es in sorted(GLOSARIO, key=lambda t: -len(t[0]))]


def traducir(txt):
    if not txt:
        return ''
    out = txt
    for pat, es in _PATRONES:
        out = pat.sub(es.upper() if txt.isupper() else es, out)
    return out
