import sqlite3
import os
DB_NAME = os.path.join(os.path.dirname(__file__), "academia.db")

def get_connection():
    print("Usando base de datos:", os.path.abspath(DB_NAME))
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS usuario (
      id INTEGER PRIMARY KEY,
      dni TEXT UNIQUE CHECK (dni IS NULL OR length(trim(dni)) > 0),
      username TEXT UNIQUE CHECK (username IS NULL OR length(trim(username)) > 0),
      nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
      apellido TEXT NOT NULL CHECK (length(trim(apellido)) > 0),
      email TEXT UNIQUE CHECK (email IS NULL OR length(trim(email)) > 0),
      estado TEXT NOT NULL CHECK (estado IN ('ACTIVO','INACTIVO')),
      rol TEXT NOT NULL CHECK (rol IN ('ALUMNO','DOCENTE','ADMIN')),
      direccion_calle TEXT,
      direccion_numero TEXT,
      direccion_ciudad TEXT,
      password TEXT,
      fecha_creacion TEXT NOT NULL DEFAULT (datetime('now'))
    );


    CREATE TABLE IF NOT EXISTS telefono (
      id_usuario INTEGER NOT NULL,
      numero TEXT NOT NULL,
      PRIMARY KEY (id_usuario, numero),
      FOREIGN KEY (id_usuario) REFERENCES usuario(id)
        ON UPDATE CASCADE ON DELETE CASCADE
    );

    CREATE UNIQUE INDEX IF NOT EXISTS ux_telefono_usuario_numero
    ON telefono(id_usuario, numero);

    CREATE TABLE IF NOT EXISTS auditoria (
      id_auditoria INTEGER PRIMARY KEY,
      fecha_hora TEXT NOT NULL,
      accion TEXT NOT NULL,
      detalle TEXT,
      estado TEXT NOT NULL,
      id_usuario INTEGER,
      FOREIGN KEY (id_usuario) REFERENCES usuario(id)
        ON UPDATE CASCADE ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS sesion (
      id INTEGER PRIMARY KEY,
      ip_equipo TEXT,
      fecha_hora_inicio TEXT NOT NULL,
      fecha_hora_fin TEXT,
      estado TEXT NOT NULL,
      id_usuario INTEGER,
      FOREIGN KEY (id_usuario) REFERENCES usuario(id)
        ON UPDATE CASCADE ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS alumno (
      id_usuario INTEGER PRIMARY KEY,
      nivel TEXT NOT NULL,
      FOREIGN KEY (id_usuario) REFERENCES usuario(id)
        ON UPDATE CASCADE ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS administrador (
      id_usuario INTEGER PRIMARY KEY,
      cargo TEXT NOT NULL,
      FOREIGN KEY (id_usuario) REFERENCES usuario(id)
        ON UPDATE CASCADE ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS docente (
      id_usuario INTEGER PRIMARY KEY,
      especialidad TEXT NOT NULL,
      FOREIGN KEY (id_usuario) REFERENCES usuario(id)
        ON UPDATE CASCADE ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS curso (
      id INTEGER PRIMARY KEY,
      nombre TEXT NOT NULL CHECK (length(trim(nombre)) > 0),
      descripcion TEXT,
      duracion_horas INTEGER NOT NULL CHECK (duracion_horas > 0),
      cupo_maximo INTEGER NOT NULL CHECK (cupo_maximo > 0),
      fecha_inicio TEXT NOT NULL CHECK (fecha_inicio GLOB '____-__-__'),
      fecha_fin TEXT CHECK (fecha_fin IS NULL OR fecha_fin GLOB '____-__-__'),
      estado TEXT NOT NULL DEFAULT 'ABIERTO' CHECK (estado IN ('ABIERTO','CERRADO')),
      id_docente INTEGER NOT NULL,
      id_administrador INTEGER NOT NULL,
      FOREIGN KEY (id_docente) REFERENCES usuario(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
      FOREIGN KEY (id_administrador) REFERENCES usuario(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
    );


    CREATE TABLE IF NOT EXISTS inscripcion (
      id INTEGER PRIMARY KEY,
      estado TEXT NOT NULL CHECK (estado IN ('PENDIENTE','CONFIRMADA','CANCELADA')),
      fecha_inscripcion TEXT NOT NULL CHECK (fecha_inscripcion GLOB '____-__-__'),
      costo REAL NOT NULL CHECK (costo >= 0),
      id_curso INTEGER NOT NULL,
      id_alumno INTEGER NOT NULL,
      FOREIGN KEY (id_curso) REFERENCES curso(id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
      FOREIGN KEY (id_alumno) REFERENCES usuario(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
    );

    CREATE UNIQUE INDEX IF NOT EXISTS idx_inscripcion_alumno_curso
      ON inscripcion(id_alumno, id_curso);

    CREATE TABLE IF NOT EXISTS pago (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      fecha_pago TEXT NOT NULL CHECK (fecha_pago GLOB '____-__-__'),
      monto REAL NOT NULL CHECK (monto > 0),
      estado_pago TEXT NOT NULL CHECK (estado_pago IN ('PENDIENTE','PAGADO','RECHAZADO')),
      metodo_pago TEXT NOT NULL CHECK (metodo_pago IN ('EFECTIVO','TRANSFERENCIA','TARJETA','MERCADO PAGO','OTRO')),
      id_inscripcion INTEGER NOT NULL UNIQUE,
      FOREIGN KEY (id_inscripcion) REFERENCES inscripcion(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
    );



    CREATE TABLE IF NOT EXISTS examen (
      id_inscripcion INTEGER PRIMARY KEY,
      nombre TEXT NOT NULL,
      tipo TEXT NOT NULL,
      fecha_examen TEXT NOT NULL,
      FOREIGN KEY (id_inscripcion) REFERENCES inscripcion(id)
        ON UPDATE CASCADE ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS nota (
      id_examen INTEGER PRIMARY KEY,
      nota REAL NOT NULL,
      fecha_registro TEXT NOT NULL,
      observacion TEXT,
      FOREIGN KEY (id_examen) REFERENCES examen(id_inscripcion)
        ON UPDATE CASCADE ON DELETE RESTRICT
    );
    """

    cursor.executescript(sql)
    conn.commit()
    conn.close()
    print("Tablas creadas correctamente.")


if __name__ == "__main__":
    create_tables()
