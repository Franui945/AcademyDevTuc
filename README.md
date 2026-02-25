erDiagram
    USUARIO {
        int id PK
        string dni
        string username
        string nombre
        string apellido
        string email
        string estado
        string rol
        string direccion_calle
        string direccion_numero
        string direccion_ciudad
        string fecha_creacion
        string password
    }

    TELEFONO {
        int id_usuario FK
        string numero
    }

    ALUMNO {
        int id_usuario PK, FK
        string nivel
    }

    DOCENTE {
        int id_usuario PK, FK
        string especialidad
    }

    ADMINISTRADOR {
        int id_usuario PK, FK
        string cargo
    }

    CURSO {
        int id PK
        string nombre
        string descripcion
        int duracion_horas
        int cupo_maximo
        string fecha_inicio
        string fecha_fin
        string estado
        int id_docente FK
        int id_administrador FK
    }

    INSCRIPCION {
        int id PK
        string estado
        string fecha_inscripcion
        float costo
        int id_curso FK
        int id_alumno FK
    }

    PAGO {
        int id PK
        string fecha_pago
        float monto
        string estado_pago
        string metodo_pago
        int id_inscripcion FK UNIQUE
    }

    EXAMEN {
        int id PK
        int id_curso FK
        string nombre
        string tipo
        string fecha_examen
    }

    NOTA {
        int id PK
        int id_examen FK
        int id_alumno FK
        float nota
        string fecha_registro
        string observacion
    }

    USUARIO ||--o{ TELEFONO : "tiene"
    USUARIO ||--o| ALUMNO : "es"
    USUARIO ||--o| DOCENTE : "es"
    USUARIO ||--o| ADMINISTRADOR : "es"

    DOCENTE ||--o{ CURSO : "dicta"
    ADMINISTRADOR ||--o{ CURSO : "administra"

    CURSO ||--o{ INSCRIPCION : "recibe"
    USUARIO ||--o{ INSCRIPCION : "se_inscribe"

    INSCRIPCION ||--o| PAGO : "pago_unico"

    CURSO ||--o{ EXAMEN : "tiene"
    EXAMEN ||--o{ NOTA : "genera"
    USUARIO ||--o{ NOTA : "obtiene"
