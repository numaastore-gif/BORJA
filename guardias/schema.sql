-- Esquema de la base de datos de soporte de guardia.
-- Dosificado de fábricas de pan (PCS7 + WinCC/SCADA).
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------- plantas
CREATE TABLE IF NOT EXISTS planta (
    id              INTEGER PRIMARY KEY,
    codigo          TEXT NOT NULL UNIQUE,      -- código corto interno, p.ej. "ANT-01"
    nombre          TEXT NOT NULL,             -- "Mercadona Antequera - Horno"
    localidad       TEXT,
    provincia       TEXT,
    cliente         TEXT DEFAULT 'Mercadona',
    tipo_linea      TEXT,                      -- pan de molde, bollería, masa madre...
    criticidad      TEXT DEFAULT 'media',      -- alta | media | baja
    horario         TEXT,                      -- turnos de producción
    acceso_remoto   TEXT,                      -- VPN, TeamViewer, salto, credenciales (dónde)
    direccion       TEXT,
    notas           TEXT,
    creado          TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    actualizado     TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS contacto (
    id          INTEGER PRIMARY KEY,
    planta_id   INTEGER NOT NULL REFERENCES planta(id) ON DELETE CASCADE,
    nombre      TEXT NOT NULL,
    rol         TEXT,                          -- jefe de turno, mantenimiento, calidad...
    telefono    TEXT,
    email       TEXT,
    horario     TEXT,
    prioridad   INTEGER NOT NULL DEFAULT 5,    -- 1 = a quien se llama primero
    notas       TEXT
);
CREATE INDEX IF NOT EXISTS ix_contacto_planta ON contacto(planta_id, prioridad);

-- ---------------------------------------------------------------- equipos
CREATE TABLE IF NOT EXISTS equipo (
    id          INTEGER PRIMARY KEY,
    planta_id   INTEGER NOT NULL REFERENCES planta(id) ON DELETE CASCADE,
    tipo        TEXT NOT NULL,                 -- AS | OS | ES | ET200 | variador | bascula | red | otro
    nombre      TEXT NOT NULL,                 -- "AS01 dosificado harinas"
    fabricante  TEXT,
    modelo      TEXT,                          -- CPU 410-5H, IPC647E...
    referencia  TEXT,                          -- MLFB / nº de pedido
    firmware    TEXT,
    ip          TEXT,
    red         TEXT,                          -- planta / terminal bus / Profibus DP1
    ubicacion   TEXT,                          -- armario, sala técnica
    repuesto    INTEGER NOT NULL DEFAULT 0,    -- 1 si hay repuesto en planta
    notas       TEXT
);
CREATE INDEX IF NOT EXISTS ix_equipo_planta ON equipo(planta_id, tipo);

CREATE TABLE IF NOT EXISTS software (
    id          INTEGER PRIMARY KEY,
    planta_id   INTEGER NOT NULL REFERENCES planta(id) ON DELETE CASCADE,
    producto    TEXT NOT NULL,                 -- SIMATIC PCS7, WinCC, STEP7, BATCH...
    version     TEXT,
    service_pack TEXT,
    licencia    TEXT,                          -- dónde está el dongle / fichero de licencia
    notas       TEXT
);
CREATE INDEX IF NOT EXISTS ix_software_planta ON software(planta_id);

-- ---------------------------------------------------------- proyectos PCS7
CREATE TABLE IF NOT EXISTS proyecto (
    id            INTEGER PRIMARY KEY,
    planta_id     INTEGER NOT NULL REFERENCES planta(id) ON DELETE CASCADE,
    nombre        TEXT NOT NULL,
    version_pcs7  TEXT,
    ruta_archivo  TEXT,                        -- ruta al .zap/.zip fuera del repositorio
    sha256        TEXT,
    tam_bytes     INTEGER,
    fecha_version TEXT,                        -- fecha de la copia archivada
    origen        TEXT,                        -- quién la entregó / de dónde salió
    notas         TEXT,
    creado        TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS ix_proyecto_planta ON proyecto(planta_id);

-- Tabla de símbolos / variables importada de STEP7-PCS7.
CREATE TABLE IF NOT EXISTS simbolo (
    id          INTEGER PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyecto(id) ON DELETE CASCADE,
    nombre      TEXT NOT NULL,
    direccion   TEXT,                          -- E 0.0, DB12.DBX3.1, FC105...
    tipo_dato   TEXT,
    comentario  TEXT
);
CREATE INDEX IF NOT EXISTS ix_simbolo_proyecto ON simbolo(proyecto_id);
CREATE INDEX IF NOT EXISTS ix_simbolo_nombre ON simbolo(nombre);
CREATE INDEX IF NOT EXISTS ix_simbolo_dir ON simbolo(direccion);

-- Contenido del archivo de proyecto (.zap/.zip), solo metadatos.
CREATE TABLE IF NOT EXISTS proyecto_entrada (
    id          INTEGER PRIMARY KEY,
    proyecto_id INTEGER NOT NULL REFERENCES proyecto(id) ON DELETE CASCADE,
    ruta        TEXT NOT NULL,
    tam_bytes   INTEGER,
    modificado  TEXT
);
CREATE INDEX IF NOT EXISTS ix_pentrada_proyecto ON proyecto_entrada(proyecto_id);

-- ------------------------------------------------- base de conocimiento de alarmas
CREATE TABLE IF NOT EXISTS alarma (
    id             INTEGER PRIMARY KEY,
    planta_id      INTEGER REFERENCES planta(id) ON DELETE CASCADE,  -- NULL = aplica a todas
    codigo         TEXT,                       -- nº de mensaje WinCC / identificador
    texto          TEXT NOT NULL,              -- texto tal cual aparece en el SCADA
    clase          TEXT,                       -- alarma, aviso, fallo del sistema...
    area           TEXT,                       -- dosificado harinas, amasado, levadura...
    equipo_id      INTEGER REFERENCES equipo(id) ON DELETE SET NULL,
    causa          TEXT,                       -- causa probable
    actuacion      TEXT,                       -- qué hacer, paso a paso
    criticidad     TEXT DEFAULT 'media',
    requiere_parada INTEGER NOT NULL DEFAULT 0,
    referencias    TEXT,                       -- planos, manuales, nº de bloque
    verificada     INTEGER NOT NULL DEFAULT 0, -- 1 = comprobada en campo
    creado         TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    actualizado    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS ix_alarma_planta ON alarma(planta_id);
CREATE INDEX IF NOT EXISTS ix_alarma_codigo ON alarma(codigo);

-- ---------------------------------------------------------------- guardias
CREATE TABLE IF NOT EXISTS guardia (
    id       INTEGER PRIMARY KEY,
    tecnico  TEXT NOT NULL,
    inicio   TEXT NOT NULL,                    -- ISO 8601
    fin      TEXT NOT NULL,
    telefono TEXT,
    notas    TEXT
);
CREATE INDEX IF NOT EXISTS ix_guardia_rango ON guardia(inicio, fin);

-- ------------------------------------------------------------- incidencias
CREATE TABLE IF NOT EXISTS incidencia (
    id             INTEGER PRIMARY KEY,
    planta_id      INTEGER NOT NULL REFERENCES planta(id) ON DELETE CASCADE,
    guardia_id     INTEGER REFERENCES guardia(id) ON DELETE SET NULL,
    equipo_id      INTEGER REFERENCES equipo(id) ON DELETE SET NULL,
    alarma_id      INTEGER REFERENCES alarma(id) ON DELETE SET NULL,
    titulo         TEXT NOT NULL,
    recibido       TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    cerrado        TEXT,
    canal          TEXT,                       -- teléfono, correo, SCADA...
    avisado_por    TEXT,
    area           TEXT,
    sintoma        TEXT,
    diagnostico    TEXT,
    solucion       TEXT,
    parada_min     INTEGER,                    -- minutos de parada de línea
    resuelto_remoto INTEGER NOT NULL DEFAULT 0,
    estado         TEXT NOT NULL DEFAULT 'abierta',   -- abierta | en curso | cerrada | seguimiento
    criticidad     TEXT DEFAULT 'media',
    acciones       TEXT,                       -- pendientes / mejora preventiva
    etiquetas      TEXT,                       -- separadas por coma
    actualizado    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS ix_incidencia_planta ON incidencia(planta_id, recibido);
CREATE INDEX IF NOT EXISTS ix_incidencia_estado ON incidencia(estado, recibido);

-- ---------------------------------------------------------------- adjuntos
CREATE TABLE IF NOT EXISTS adjunto (
    id          INTEGER PRIMARY KEY,
    entidad     TEXT NOT NULL,                 -- planta | incidencia | alarma | proyecto
    entidad_id  INTEGER NOT NULL,
    nombre      TEXT NOT NULL,
    ruta        TEXT NOT NULL,
    tipo_mime   TEXT,
    tam_bytes   INTEGER,
    descripcion TEXT,
    creado      TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS ix_adjunto_entidad ON adjunto(entidad, entidad_id);

-- ------------------------------------------------------------- búsqueda FTS
-- Índice unificado: se alimenta con disparadores desde alarma e incidencia.
CREATE VIRTUAL TABLE IF NOT EXISTS busqueda USING fts5(
    entidad UNINDEXED,
    entidad_id UNINDEXED,
    titulo,
    cuerpo,
    tokenize = "unicode61 remove_diacritics 2"
);

CREATE TRIGGER IF NOT EXISTS trg_alarma_ai AFTER INSERT ON alarma BEGIN
    INSERT INTO busqueda(entidad, entidad_id, titulo, cuerpo)
    VALUES ('alarma', new.id, coalesce(new.codigo,'') || ' ' || new.texto,
            coalesce(new.causa,'') || ' ' || coalesce(new.actuacion,'') || ' ' ||
            coalesce(new.area,'') || ' ' || coalesce(new.referencias,''));
END;
CREATE TRIGGER IF NOT EXISTS trg_alarma_ad AFTER DELETE ON alarma BEGIN
    DELETE FROM busqueda WHERE entidad='alarma' AND entidad_id=old.id;
END;
CREATE TRIGGER IF NOT EXISTS trg_alarma_au AFTER UPDATE ON alarma BEGIN
    DELETE FROM busqueda WHERE entidad='alarma' AND entidad_id=old.id;
    INSERT INTO busqueda(entidad, entidad_id, titulo, cuerpo)
    VALUES ('alarma', new.id, coalesce(new.codigo,'') || ' ' || new.texto,
            coalesce(new.causa,'') || ' ' || coalesce(new.actuacion,'') || ' ' ||
            coalesce(new.area,'') || ' ' || coalesce(new.referencias,''));
END;

CREATE TRIGGER IF NOT EXISTS trg_incidencia_ai AFTER INSERT ON incidencia BEGIN
    INSERT INTO busqueda(entidad, entidad_id, titulo, cuerpo)
    VALUES ('incidencia', new.id, new.titulo,
            coalesce(new.sintoma,'') || ' ' || coalesce(new.diagnostico,'') || ' ' ||
            coalesce(new.solucion,'') || ' ' || coalesce(new.etiquetas,''));
END;
CREATE TRIGGER IF NOT EXISTS trg_incidencia_ad AFTER DELETE ON incidencia BEGIN
    DELETE FROM busqueda WHERE entidad='incidencia' AND entidad_id=old.id;
END;
CREATE TRIGGER IF NOT EXISTS trg_incidencia_au AFTER UPDATE ON incidencia BEGIN
    DELETE FROM busqueda WHERE entidad='incidencia' AND entidad_id=old.id;
    INSERT INTO busqueda(entidad, entidad_id, titulo, cuerpo)
    VALUES ('incidencia', new.id, new.titulo,
            coalesce(new.sintoma,'') || ' ' || coalesce(new.diagnostico,'') || ' ' ||
            coalesce(new.solucion,'') || ' ' || coalesce(new.etiquetas,''));
END;
