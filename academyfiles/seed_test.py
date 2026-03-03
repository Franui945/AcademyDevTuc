# seed_demo.py
from services import (
    hash_password,
    crear_usuario, crear_rol_alumno, crear_rol_docente, crear_rol_admin,
    agregar_telefono,
)
from models import Usuario, Alumno, Docente, Administrador, Telefono

def crear_usuario_con_rol(*, dni, username, nombre, apellido, email, rol, password, tel=None,
                          nivel=None, especialidad=None, cargo=None):
    u = Usuario(
        dni=str(dni),
        username=username,
        nombre=nombre,
        apellido=apellido,
        email=email,
        rol=rol,
        estado="ACTIVO",
        password=hash_password(password),
    )
    user_id = crear_usuario(u)

    # Rol específico
    if rol == "ALUMNO":
        crear_rol_alumno(Alumno(id_usuario=user_id, nivel=nivel or "Principiante"))
    elif rol == "DOCENTE":
        crear_rol_docente(Docente(id_usuario=user_id, especialidad=especialidad or "Programación"))
    elif rol == "ADMIN":
        crear_rol_admin(Administrador(id_usuario=user_id, cargo=cargo or "BÁSICO"))

    # Teléfono (opcional)
    if tel:
        agregar_telefono(Telefono(id_usuario=user_id, numero=str(tel)))

    return user_id

def main():
    # Password única para demo (la decís en la entrega)
    PASS = "DevTuc123"

    # ADMIN
    admin_id = crear_usuario_con_rol(
        dni=40000001, username="admin", nombre="Admin", apellido="DevTuc",
        email="admin@devtuc.local", rol="ADMIN", password=PASS, tel="3816000001", cargo="TOTAL"
    )

    # DOCENTES
    doc1_id = crear_usuario_con_rol(
        dni=40000002, username="docente1", nombre="Sofía", apellido="Herrera",
        email="sofia.herrera@devtuc.local", rol="DOCENTE", password=PASS, tel="3816000002",
        especialidad="Bases de Datos"
    )
    doc2_id = crear_usuario_con_rol(
        dni=40000003, username="docente2", nombre="Matías", apellido="López",
        email="matias.lopez@devtuc.local", rol="DOCENTE", password=PASS, tel="3816000003",
        especialidad="Programación"
    )

    # ALUMNOS
    a1_id = crear_usuario_con_rol(
        dni=40000004, username="alumno1", nombre="Juan", apellido="Paz",
        email="juan.paz@devtuc.local", rol="ALUMNO", password=PASS, tel="3816000004",
        nivel="Principiante"
    )
    a2_id = crear_usuario_con_rol(
        dni=40000005, username="alumno2", nombre="Lucía", apellido="Gómez",
        email="lucia.gomez@devtuc.local", rol="ALUMNO", password=PASS, tel="3816000005",
        nivel="Intermedio"
    )
    a3_id = crear_usuario_con_rol(
        dni=40000006, username="alumno3", nombre="Nicolás", apellido="Ríos",
        email="nicolas.rios@devtuc.local", rol="ALUMNO", password=PASS, tel="3816000006",
        nivel="Avanzado"
    )

    print("✅ Usuarios demo creados:")
    print("ADMIN:", admin_id, "DOCENTES:", doc1_id, doc2_id, "ALUMNOS:", a1_id, a2_id, a3_id)
    print("🔑 Password para todos:", PASS)

if __name__ == "__main__":
    main()