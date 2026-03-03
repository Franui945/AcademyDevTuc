# services.py
import sqlite3
import hashlib
import os
from typing import Optional, Any, Dict, Tuple, List
import datetime
from datetime import date

from database import get_connection
from models import (
    Usuario,
    Telefono,
    Alumno,
    Administrador,
    Docente,
    Inscripcion,
    Pago,
    Examen,
    Nota,
)

# ======================================================
# SEGURIDAD / PASSWORD
# ======================================================

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    salt_hex = salt.hex()
    hash_hex = hashlib.sha256(salt + password.encode()).hexdigest()
    return f"{salt_hex}${hash_hex}"


def verify_password(password: str, stored_password: str) -> bool:
    try:
        salt_hex, hash_hex = stored_password.split("$")
        salt = bytes.fromhex(salt_hex)
    except Exception:
        return False

    return hashlib.sha256(salt + password.encode()).hexdigest() == hash_hex


def password_strength(password: str) -> Tuple[bool, str]:
    if len(password) < 8:
        return False, "Debe tener al menos 8 caracteres."
    if not any(c.isdigit() for c in password):
        return False, "Debe contener al menos un número."
    if not any(c.isalpha() for c in password):
        return False, "Debe contener al menos una letra."
    return True, ""


# ======================================================
# HELPERS DB
# ======================================================

def insert_and_get_id(conn: sqlite3.Connection, table: str, data: Dict[str, Any]) -> int:
    cols = ", ".join(data.keys())
    placeholders = ", ".join([f":{k}" for k in data.keys()])
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    cur = conn.execute(sql, data)
    return cur.lastrowid


def insert(conn: sqlite3.Connection, table: str, data: Dict[str, Any]) -> None:
    cols = ", ".join(data.keys())
    placeholders = ", ".join([f":{k}" for k in data.keys()])
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    conn.execute(sql, data)


def update(conn: sqlite3.Connection, table: str, data: Dict[str, Any], where: str, params: tuple):
    sets = ", ".join([f"{k}=?" for k in data.keys()])
    sql = f"UPDATE {table} SET {sets} WHERE {where}"
    conn.execute(sql, tuple(data.values()) + params)


# ======================================================
# USUARIOS
# ======================================================

def crear_usuario(usuario: Usuario) -> int:
    conn = get_connection()
    try:
        with conn:
            data = usuario.to_dict()
            data.pop("fecha_creacion", None)
            return insert_and_get_id(conn, "usuario", data)
    finally:
        conn.close()


def obtener_usuario_por_id(user_id: int) -> Optional[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute("SELECT * FROM usuario WHERE id = ?", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def obtener_usuario_por_username(username: str) -> Optional[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute("SELECT * FROM usuario WHERE username = ?", (username,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def desactivar_usuario(user_id: int):
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "UPDATE usuario SET estado = 'INACTIVO' WHERE id = ?",
                (user_id,)
            )
    finally:
        conn.close()


# ======================================================
# ROLES
# ======================================================

def crear_rol_alumno(alumno: Alumno):
    conn = get_connection()
    try:
        with conn:
            insert(conn, "alumno", alumno.to_dict())
    finally:
        conn.close()


def crear_rol_admin(admin: Administrador):
    conn = get_connection()
    try:
        with conn:
            insert(conn, "administrador", admin.to_dict())
    finally:
        conn.close()


def crear_rol_docente(docente: Docente):
    conn = get_connection()
    try:
        with conn:
            insert(conn, "docente", docente.to_dict())
    finally:
        conn.close()


# ======================================================
# CURSOS
# ======================================================

def listar_cursos():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            SELECT
                id,
                nombre,
                descripcion,
                duracion_horas,
                cupo_maximo,
                fecha_inicio,
                fecha_fin,
                estado,
                id_docente,
                id_administrador
            FROM curso
            ORDER BY nombre;
            """
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def crear_curso_service(
    nombre: str,
    descripcion: Optional[str],
    duracion_horas: int,
    cupo_maximo: int,
    fecha_inicio: str,
    fecha_fin: Optional[str],
    id_docente: int,
    id_administrador: int
) -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO curso
            (nombre, descripcion, duracion_horas, cupo_maximo, fecha_inicio, fecha_fin, estado, id_docente, id_administrador)
            VALUES (?, ?, ?, ?, ?, ?, 'ABIERTO', ?, ?)
            """,
            (nombre, descripcion, duracion_horas, cupo_maximo, fecha_inicio, fecha_fin, id_docente, id_administrador)
        )
        conn.commit()
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()






# ======================================================
# INSCRIPCIONES
# ======================================================

def alumno_ya_inscripto(id_alumno: int, id_curso: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT 1 FROM inscripcion WHERE id_alumno = ? AND id_curso = ?",
            (id_alumno, id_curso)
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def inscribir_alumno(insc: Inscripcion) -> int:
    if alumno_ya_inscripto(insc.id_alumno, insc.id_curso):
        raise ValueError("El alumno ya está inscripto en este curso.")

    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            # 1) curso existe y está abierto
            cur = conn.execute(
                "SELECT cupo_maximo, estado FROM curso WHERE id = ?",
                (insc.id_curso,)
            )
            curso = cur.fetchone()
            if not curso:
                raise ValueError("El curso no existe.")
            if (curso["estado"] or "").upper() != "ABIERTO":
                raise ValueError("No se puede inscribir: el curso no está ABIERTO.")

            # 2) cupo disponible (cuenta inscripciones activas)
            cur = conn.execute(
                """
                SELECT COUNT(*) AS cant
                FROM inscripcion
                WHERE id_curso = ?
                  AND estado IN ('PENDIENTE', 'CONFIRMADA')
                """,
                (insc.id_curso,)
            )
            cant = cur.fetchone()["cant"]
            if cant >= int(curso["cupo_maximo"]):
                raise ValueError("No hay cupo disponible para este curso.")

            # 3) insertar
            return insert_and_get_id(conn, "inscripcion", insc.to_dict())
    finally:
        conn.close()





# ======================================================
# PAGOS
# ======================================================

def registrar_pago(pago: Pago) -> int:
    conn = get_connection()
    try:
        with conn:
            return insert_and_get_id(conn, "pago", pago.to_dict())
    finally:
        conn.close()


def listar_pagos_por_alumno(id_alumno: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                p.id AS id_pago,
                c.nombre AS curso,
                i.fecha_inscripcion,
                i.costo,
                p.estado_pago,
                p.metodo_pago,
                p.fecha_pago
            FROM pago p
            JOIN inscripcion i ON i.id = p.id_inscripcion
            JOIN curso c ON c.id = i.id_curso
            WHERE i.id_alumno = ?
            ORDER BY COALESCE(p.fecha_pago, i.fecha_inscripcion) DESC
        """, (id_alumno,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# =========================
# EXÁMENES
# =========================

def crear_examen(ex: Examen) -> int:
    conn = get_connection()
    try:
        with conn:
            data = ex.to_dict()
            data.pop("id", None)  # por si viene
            return insert_and_get_id(conn, "examen", data)
    finally:
        conn.close()


def crear_examen_service(ex: Examen) -> Tuple[bool, Optional[str]]:
    nombre = (ex.nombre or "").strip()
    tipo = (ex.tipo or "").strip().upper()
    fecha = (ex.fecha_examen or "").strip()

    if not ex.id_curso:
        return False, "Curso inválido."
    if not nombre:
        return False, "El nombre del examen es obligatorio."
    if not fecha:
        return False, "La fecha del examen es obligatoria."
    try:
        date.fromisoformat(fecha)
    except Exception:
        return False, "Fecha inválida. Usá YYYY-MM-DD."

    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO examen (id_curso, nombre, tipo, fecha_examen)
                VALUES (?, ?, ?, ?)
                """,
                (int(ex.id_curso), nombre, tipo, fecha)
            )
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def listar_examenes_por_curso(id_curso: int) -> List[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        # 1) Ver columnas reales de la tabla examen
        cols = conn.execute("PRAGMA table_info(examen);").fetchall()
        if not cols:
            raise sqlite3.OperationalError("La tabla 'examen' no existe o no tiene columnas.")

        colnames = {c["name"] for c in cols}

        # 2) Elegir la PK correcta (según tu DB puede ser 'id' o 'id_inscripcion')
        if "id" in colnames:
            pk = "id"
        elif "id_inscripcion" in colnames:
            pk = "id_inscripcion"
        else:
            # si no hay ninguna de esas, usamos la primera PK marcada
            pk_candidates = [c["name"] for c in cols if c["pk"] == 1]
            pk = pk_candidates[0] if pk_candidates else None

        if not pk:
            raise sqlite3.OperationalError("No se encontró columna PK en 'examen'.")

        # 3) SELECT normalizando el id SIEMPRE como 'id'
        cur = conn.execute(
            f"""
            SELECT
                {pk} AS id,
                nombre,
                tipo,
                fecha_examen,
                id_curso
            FROM examen
            WHERE id_curso = ?
            ORDER BY fecha_examen DESC, nombre;
            """,
            (int(id_curso),)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

# Para Docente: ver inscriptos (para cargar notas)
def listar_inscriptos_por_curso(id_curso: int) -> List[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            SELECT
                u.id AS id_alumno,
                u.nombre || ' ' || u.apellido AS alumno,
                i.estado AS estado_insc,
                i.id AS id_inscripcion
            FROM inscripcion i
            JOIN usuario u ON u.id = i.id_alumno
            WHERE i.id_curso = ?
              AND i.estado IN ('PENDIENTE','CONFIRMADA')
            ORDER BY u.apellido, u.nombre;
            """,
            (int(id_curso),)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


# =========================
# NOTAS
# =========================

def guardar_nota_service(n: Nota) -> Tuple[bool, Optional[str]]:
    if not n.id_examen or not n.id_alumno:
        return False, "Examen o alumno inválido."

    try:
        nota_val = float(n.nota)
    except Exception:
        return False, "Nota inválida."

    if nota_val < 0 or nota_val > 10:
        return False, "La nota debe estar entre 0 y 10."

    fecha = (n.fecha_registro or "").strip() or str(date.today())
    try:
        date.fromisoformat(fecha)
    except Exception:
        return False, "Fecha inválida. Usá YYYY-MM-DD."

    obs = (n.observacion or "").strip() or None

    conn = get_connection()
    try:
        with conn:
            # UPSERT: si ya existe (id_examen,id_alumno), actualiza
            conn.execute(
                """
                INSERT INTO nota (id_examen, id_alumno, nota, fecha_registro, observacion)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id_examen, id_alumno)
                DO UPDATE SET
                    nota = excluded.nota,
                    fecha_registro = excluded.fecha_registro,
                    observacion = excluded.observacion
                """,
                (int(n.id_examen), int(n.id_alumno), float(nota_val), fecha, obs)
            )
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def listar_notas_por_alumno(id_alumno: int) -> List[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            """
            SELECT
                n.id,
                c.nombre AS curso,
                e.nombre AS examen,
                e.tipo,
                e.fecha_examen,
                n.nota,
                n.fecha_registro,
                n.observacion
            FROM nota n
            JOIN examen e ON e.id = n.id_examen
            JOIN curso c ON c.id = e.id_curso
            WHERE n.id_alumno = ?
            ORDER BY e.fecha_examen DESC, c.nombre, e.nombre;
            """,
            (int(id_alumno),)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()



# ======================================================
# LOGIN
# ======================================================

def verificar_login(username: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    if not username or not password:
        return False, "Usuario y contraseña obligatorios.", None

    conn = get_connection()
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.execute(
            "SELECT * FROM usuario WHERE username = ?",
            (username,)
        )
        row = cur.fetchone()

        if not row:
            return False, "Usuario no encontrado.", None

        if row["estado"] != "ACTIVO":
            return False, "Usuario inactivo.", None

        if not verify_password(password, row["password"]):
            return False, "Contraseña incorrecta.", None

        return True, "Login correcto.", dict(row)

    except Exception as e:
        return False, f"Error de login: {e}", None

    finally:
        conn.close()

def guardar_o_actualizar_pago(
    id_inscripcion,
    estado_pago,
    metodo_pago,
    fecha_pago,
    monto,
    id_pago=None
):
    conn = get_connection()
    try:
        cur = conn.cursor()

        if id_pago is None:
            cur.execute(
                """
                INSERT INTO pago
                (id_inscripcion, estado_pago, metodo_pago, fecha_pago, monto)
                VALUES (?, ?, ?, ?, ?)
                """,
                (id_inscripcion, estado_pago, metodo_pago, fecha_pago, monto)
            )
        else:
            cur.execute(
                """
                UPDATE pago
                SET estado_pago = ?, metodo_pago = ?, fecha_pago = ?, monto = ?
                WHERE id = ?
                """,
                (estado_pago, metodo_pago, fecha_pago, monto, id_pago)
            )

        conn.commit()
        return True, None

    except Exception as e:
        return False, str(e)

    finally:
        conn.close()

def obtener_id_inscripcion_por_pago(id_pago: int):
    """
    Devuelve el id_inscripcion asociado a un pago.
    Si no existe, devuelve None.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id_inscripcion FROM pago WHERE id = ?",
            (id_pago,)
        )
        row = cur.fetchone()
        return row["id_inscripcion"] if row else None
    finally:
        conn.close()

def listar_inscripciones_alumno(id_alumno: int) -> List[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                i.id,
                c.nombre AS curso,
                i.fecha_inscripcion,
                i.estado,
                i.costo,
                p.estado_pago,
                p.metodo_pago,
                p.fecha_pago
            FROM inscripcion i
            JOIN curso c ON c.id = i.id_curso
            LEFT JOIN pago p ON p.id_inscripcion = i.id
            WHERE i.id_alumno = ?
            ORDER BY i.fecha_inscripcion DESC, c.nombre;
        """, (id_alumno,))
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()










def editar_curso_service(
    id_curso: int,
    nombre: str,
    descripcion: Optional[str],
    duracion_horas: int,
    cupo_maximo: int,
    fecha_inicio: str,
    fecha_fin: Optional[str],
    id_docente: int,
    id_administrador: int,
    estado: str
) -> Tuple[bool, Optional[str]]:
    # Validaciones mínimas (evitan romper la BD con valores inválidos)
    nombre = (nombre or "").strip()
    estado = (estado or "").strip().upper()

    if not nombre:
        return False, "El nombre es obligatorio."
    if duracion_horas <= 0:
        return False, "La duración (horas) debe ser mayor a 0."
    if cupo_maximo <= 0:
        return False, "El cupo máximo debe ser mayor a 0."
    if not fecha_inicio or not str(fecha_inicio).strip():
        return False, "La fecha de inicio es obligatoria."

    estados_validos = {"ABIERTO", "CERRADO"}
    if estado not in estados_validos:
        return False, f"Estado inválido. Debe ser uno de: {', '.join(sorted(estados_validos))}."

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE curso
            SET
                nombre = ?,
                descripcion = ?,
                duracion_horas = ?,
                cupo_maximo = ?,
                fecha_inicio = ?,
                fecha_fin = ?,
                id_docente = ?,
                id_administrador = ?,
                estado = ?
            WHERE id = ?
            """,
            (
                nombre,
                descripcion,
                int(duracion_horas),
                int(cupo_maximo),
                fecha_inicio.strip(),
                (fecha_fin.strip() if isinstance(fecha_fin, str) and fecha_fin.strip() else None),
                int(id_docente),
                int(id_administrador),
                estado,
                int(id_curso),
            )
        )

        if cur.rowcount == 0:
            return False, "El curso no existe."

        conn.commit()
        return True, None

    except sqlite3.IntegrityError as e:
        # FK / UNIQUE / CHECK
        msg = str(e).lower()
        if "foreign key constraint failed" in msg:
            return False, "Docente o Administrador inválido (no existe en la base)."
        if "check constraint failed" in msg:
            return False, "Algún dato no cumple las reglas (CHECK) de la base."
        if "unique constraint failed" in msg:
            return False, "Se violó una restricción UNIQUE en la base."
        return False, str(e)

    except Exception as e:
        return False, str(e)

    finally:
        conn.close()


def cerrar_curso_service(id_curso: int):
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "UPDATE curso SET estado = 'CERRADO' WHERE id = ? AND estado <> 'CERRADO'",
                (id_curso,)
            )
            if cur.rowcount == 0:
                # puede ser que no exista o ya esté cerrado
                # opcional: chequear existencia
                cur2 = conn.execute("SELECT 1 FROM curso WHERE id = ?", (id_curso,))
                if cur2.fetchone() is None:
                    return False, "El curso no existe."
                return False, "El curso ya está cerrado."
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ======================================================
# INSCRIPCIONES (ADMIN / ALUMNO)
# ======================================================

def listar_inscripciones_admin() -> List[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                i.id,
                u.nombre || ' ' || u.apellido AS alumno,
                c.nombre AS curso,
                i.fecha_inscripcion,
                i.estado AS estado,              
                i.costo,
                p.estado_pago,
                p.metodo_pago,
                p.fecha_pago
            FROM inscripcion i
            JOIN usuario u ON u.id = i.id_alumno
            JOIN curso c ON c.id = i.id_curso
            LEFT JOIN pago p ON p.id_inscripcion = i.id
            ORDER BY i.fecha_inscripcion DESC, alumno, curso;
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()




def cancelar_inscripcion_alumno(id_inscripcion: int) -> bool:
    """
    Cancela SOLO si está en estado PENDIENTE.
    (El control de pertenencia al alumno lo hacés en la UI por sesión.)
    """
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "UPDATE inscripcion SET estado = 'CANCELADA' WHERE id = ? AND estado = 'PENDIENTE'",
                (id_inscripcion,)
            )
            return cur.rowcount > 0
    finally:
        conn.close()


def listar_cursos_admin() -> List[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                c.id,
                c.nombre,
                c.fecha_inicio,
                c.fecha_fin,
                c.cupo_maximo,
                c.estado,
                TRIM(
                    COALESCE(d.nombre, '') || ' ' || COALESCE(d.apellido, '')
                ) AS docente
            FROM curso c
            LEFT JOIN usuario d ON d.id = c.id_docente
            ORDER BY c.fecha_inicio DESC, c.nombre;
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()



def listar_pagos_admin() -> List[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                p.id AS id_pago,
                i.id AS id_inscripcion,
                u.nombre || ' ' || u.apellido AS alumno,
                c.nombre AS curso,
                i.fecha_inscripcion,
                i.costo,
                p.estado_pago,
                p.metodo_pago,
                p.fecha_pago,
                p.monto
            FROM pago p
            JOIN inscripcion i ON i.id = p.id_inscripcion
            JOIN usuario u ON u.id = i.id_alumno
            JOIN curso c ON c.id = i.id_curso
            ORDER BY COALESCE(p.fecha_pago, i.fecha_inscripcion) DESC, alumno, curso;
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def obtener_pago_admin_detalle(id_pago: int) -> Optional[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                p.*,
                u.nombre AS nombre_alumno,
                u.apellido AS apellido_alumno,
                c.nombre AS nombre_curso,
                i.fecha_inscripcion AS fecha_inscripcion,
                i.costo AS costo
            FROM pago p
            JOIN inscripcion i ON i.id = p.id_inscripcion
            JOIN usuario u ON u.id = i.id_alumno
            JOIN curso c ON c.id = i.id_curso
            WHERE p.id = ?;
        """, (id_pago,))
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def eliminar_pago_admin(id_pago: int) -> Tuple[bool, Optional[str]]:
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute("DELETE FROM pago WHERE id = ?", (id_pago,))
            if cur.rowcount == 0:
                return False, "El pago no existe."
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()



def cambiar_estado_inscripcion_admin(id_inscripcion: int, nuevo_estado: str) -> bool:
    nuevo_estado = (nuevo_estado or "").strip().upper()
    estados_validos = {"PENDIENTE", "CONFIRMADA", "CANCELADA"}
    if nuevo_estado not in estados_validos:
        raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(sorted(estados_validos))}")

    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "UPDATE inscripcion SET estado = ? WHERE id = ?",
                (nuevo_estado, id_inscripcion)
            )
            return cur.rowcount > 0
    finally:
        conn.close()




# ======================================================
# HELPERS PARA EL FORM DE INSCRIPCIÓN
# ======================================================

def listar_alumnos() -> List[Dict]:
    """
    Devuelve alumnos (id + nombre completo).
    Requiere tabla alumno (id_usuario) y usuario (id,nombre,apellido,estado)
    Ajustá nombres de columnas si tu esquema difiere.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                u.id AS id,
                u.nombre,
                u.apellido,
                u.nombre || ' ' || u.apellido AS alumno
            FROM alumno a
            JOIN usuario u ON u.id = a.id_usuario
            WHERE u.estado = 'ACTIVO'
            ORDER BY u.apellido, u.nombre;
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def listar_cursos_abiertos() -> List[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, nombre, cupo_maximo, fecha_inicio, fecha_fin, estado
            FROM curso
            WHERE estado = 'ABIERTO'
            ORDER BY fecha_inicio DESC, nombre;
        """)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

# ======================================================
# TELEFONOS
# ======================================================

def agregar_telefono(tel: Telefono) -> Tuple[bool, Optional[str]]:
    numero = (tel.numero or "").strip()
    if not numero:
        return False, "El número es obligatorio."

    conn = get_connection()
    try:
        with conn:
            conn.execute(
                "INSERT INTO telefono (id_usuario, numero) VALUES (?, ?)",
                (int(tel.id_usuario), numero)
            )
        return True, None

    except sqlite3.IntegrityError as e:
        msg = str(e).lower()
        if "unique" in msg:
            return False, "Ese teléfono ya está cargado para el usuario."
        if "foreign key" in msg:
            return False, "Usuario inválido (no existe)."
        return False, str(e)

    except Exception as e:
        return False, str(e)

    finally:
        conn.close()

def listar_telefonos_por_usuario(id_usuario: int) -> List[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(
            "SELECT numero FROM telefono WHERE id_usuario = ? ORDER BY numero;",
            (int(id_usuario),)
        )
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

def eliminar_telefono(id_usuario: int, numero: str) -> Tuple[bool, Optional[str]]:
    numero = (numero or "").strip()
    if not numero:
        return False, "Número inválido."
    
    conn = get_connection()
    try:
        with conn:
            cur = conn.execute(
                "DELETE FROM telefono WHERE id_usuario = ? AND numero = ?",
                (int(id_usuario), numero)
            )
            if cur.rowcount == 0:
                return False, "No se encontró ese teléfono para este usuario."
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
    
def registrar_nota(nota: Nota) -> Tuple[bool, Optional[str]]:
    """
    Inserta una nota en la tabla 'nota'.
    Devuelve (True, None) si ok, o (False, "mensaje") si falla.

    Requiere que exista la tabla:
      nota(id INTEGER PK, id_examen INTEGER, id_alumno INTEGER, nota REAL, fecha_registro TEXT, observacion TEXT)
    """
    conn = get_connection()
    try:
        with conn:
            conn.execute(
                """
                INSERT INTO nota (id_examen, id_alumno, nota, fecha_registro, observacion)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    int(nota.id_examen),
                    int(nota.id_alumno),
                    float(nota.nota),
                    str(nota.fecha_registro),
                    nota.observacion,
                )
            )
        return True, None

    except sqlite3.IntegrityError as e:
        msg = str(e).lower()
        if "foreign key" in msg:
            return False, "Examen o alumno inválido (no existe)."
        if "unique" in msg:
            return False, "Ya existe una nota para ese alumno en ese examen."
        return False, str(e)

    except Exception as e:
        return False, str(e)

    finally:
        conn.close()

def debug_listar_examenes():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute("SELECT * FROM examen ORDER BY id DESC;")
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()






