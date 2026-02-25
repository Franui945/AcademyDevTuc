# models.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

def _clean(d: Dict[str, Any]) -> Dict[str, Any]:
    """Quita claves con None (útil para INSERT dinámicos)."""
    return {k: v for k, v in d.items() if v is not None}



@dataclass
class Usuario:
    id: Optional[int] = None
    dni: Optional[str] = None
    username: Optional[str] = None
    nombre: str = ""
    apellido: str = ""
    email: Optional[str] = None
    estado: str = "ACTIVO"                 
    rol: str = "ALUMNO"                    
    direccion_calle: Optional[str] = None
    direccion_numero: Optional[str] = None
    direccion_ciudad: Optional[str] = None
    fecha_creacion: Optional[str] = None
    password: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Telefono:
    id_usuario: int
    numero: str
    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Auditoria:
    id_auditoria: Optional[int] = None
    fecha_hora: str = ""     # 'YYYY-MM-DD HH:MM:SS'
    accion: str = ""
    detalle: Optional[str] = None
    estado: str = "EXITO"
    id_usuario: Optional[int] = None
    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Sesion:
    id: Optional[int] = None
    ip_equipo: Optional[str] = None
    fecha_hora_inicio: str = ""
    fecha_hora_fin: Optional[str] = None
    estado: str = "ACTIVA"
    id_usuario: Optional[int] = None
    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Alumno:
    id_usuario: int
    nivel: str
    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Administrador:
    id_usuario: int
    cargo: str
    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Docente:
    id_usuario: int
    especialidad: str
    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Curso:
    id: Optional[int] = None
    nombre: str = ""
    descripcion: Optional[str] = None
    duracion_horas: int = 0
    cupo_maximo: int = 0
    fecha_inicio: str = ""   # 'YYYY-MM-DD'
    fecha_fin: Optional[str] = None
    estado: str = "ABIERTO"
    id_docente: Optional[int] = None
    id_administrador: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Inscripcion:
    id: Optional[int] = None
    estado: str = "PENDIENTE"
    fecha_inscripcion: str = ""  # 'YYYY-MM-DD'
    costo: float = 0.0
    id_curso: int = 0
    id_alumno: int = 0
    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Pago:
    id: Optional[int] = None
    fecha_pago: str = ""     # obligatorio (Opción B)
    monto: float = 0.0
    estado_pago: str = "PENDIENTE"
    metodo_pago: str = "EFECTIVO"
    id_inscripcion: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Examen:
    id_inscripcion: int
    nombre: str
    tipo: str
    fecha_examen: str         # 'YYYY-MM-DD'
    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))

@dataclass
class Nota:
    id_examen: int
    nota: float
    fecha_registro: str       # 'YYYY-MM-DD'
    observacion: Optional[str] = None
    def to_dict(self) -> Dict[str, Any]:
        return _clean(asdict(self))
