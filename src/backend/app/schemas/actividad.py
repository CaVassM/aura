"""Actividad en vivo: lo que hacen los estudiantes mientras se mira el panel de Coordinación."""

from typing import Literal

from pydantic import BaseModel, Field



class ServicioEvento(BaseModel):
    service_id: str
    nombre: str
    tipo: str
    tipo_label: str
    distrito: str


class OcupacionEvento(BaseModel):
    """Ocupación del servicio (cupos reservados / cupos liberados de la agenda abierta) tras el evento."""

    pct: float
    antes_pct: float = Field(description="Ocupación justo antes del evento")
    reservados: int
    liberados: int
    nivel: Literal["baja", "media", "alta"]


class CitaEvento(BaseModel):
    cita_id: str
    fecha: str = Field(description="Fecha de la cita (AAAA-MM-DD)")
    hora_inicio: str
    hora_fin: str
    canal: str
    canal_label: str
    dias_espera: int | None = None
    es_alternativa: bool = False


class DesencuentroEvento(BaseModel):
    registro_id: str
    motivo: str
    motivo_label: str
    servicio_ideal: str
    servicio_ideal_label: str
    distrito: str
    grupo: str
    grupo_label: str
    franjas: str = Field(description="Texto legible, p. ej. «lunes 03:00–04:00»")
    canales: list[str]


class EventoActividad(BaseModel):
    id: int
    tipo: Literal["cita_reservada", "cita_cancelada", "desencuentro"]
    registrado_en: str = Field(description="Instante real del registro (ISO, UTC)")
    fecha_solicitud: str = Field(description="Fecha simulada de la demo en que ocurrió (`hoy`)")
    origen: Literal["chat", "api"]
    estudiante_id: str
    servicio: ServicioEvento | None = None
    ocupacion: OcupacionEvento | None = None
    cita: CitaEvento | None = None
    desencuentro: DesencuentroEvento | None = None


class ActividadOut(BaseModel):
    epoca: str = Field(description="Cambia cuando se reinicia la demo")
    ultimo_id: int
    eventos: list[EventoActividad]
