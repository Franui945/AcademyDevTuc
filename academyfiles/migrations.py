import sqlite3
from database import get_connection

def migrar_pago_unico():
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pago';")
        if cur.fetchone() is None:
            print("No existe tabla 'pago'. No hay nada para migrar.")
            return

        cur.execute("PRAGMA index_list('pago');")
        indexes = cur.fetchall()
        for idx in indexes:

            if idx[1] == "ux_pago_inscripcion" and idx[2] == 1:
                print("La tabla 'pago' ya tiene UNIQUE por inscripción. Migración ya aplicada.")
                return

        cur.execute("PRAGMA foreign_keys = OFF;")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS pago_nuevo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_pago TEXT NOT NULL,
            monto REAL NOT NULL DEFAULT 0,
            estado_pago TEXT NOT NULL,
            metodo_pago TEXT NOT NULL,
            id_inscripcion INTEGER NOT NULL UNIQUE,
            FOREIGN KEY (id_inscripcion) REFERENCES inscripcion(id)
                ON UPDATE CASCADE ON DELETE CASCADE
        );
        """)

        cur.execute("""
        INSERT INTO pago_nuevo (id, id_inscripcion, fecha_pago, monto, estado_pago, metodo_pago)
        SELECT
            id,
            id_inscripcion,
            COALESCE(fecha_pago, date('now')),
            COALESCE(monto, 0),
            COALESCE(estado_pago, 'PENDIENTE'),
            COALESCE(metodo_pago, 'OTRO')
        FROM pago;
        """)

        cur.execute("DROP TABLE IF EXISTS pago;")
        cur.execute("ALTER TABLE pago_nuevo RENAME TO pago;")

        cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_pago_inscripcion
        ON pago(id_inscripcion);
        """)

        cur.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

        print("Migración de tabla 'pago' completada exitosamente.")

    except sqlite3.Error as e:
        print(f"Error durante la migración: {e}")
    finally:
        conn.close()