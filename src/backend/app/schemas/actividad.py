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
    en_lote: bool = Field(default=False, description="¿Está en modo lote (utilización ≥ umbral)?")


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


class EsperaEvento(BaseModel):
    id: str
    motivo_label: str
    servicio_ideal: str
    servicio_ideal_label: str
    distrito: str
    franjas: str
    cupo: str | None = Field(default=None, description="Solo en `lista_espera_aviso`: el cupo del que se avisó")


class LoteEvento(BaseModel):
    id: int
    estado: Literal["abierto", "resuelto"]
    solicitudes: int
    tamano_maximo: int
    ventana_s: int
    cierra_en: str | None = None
    resultado: dict | None = Field(default=None, description="Solo al resolverse: resumen del lote")


class EventoActividad(BaseModel):
    id: int
    tipo: Literal[
        "cita_reservada",
        "cita_cancelada",
        "desencuentro",
        "servicio_en_lote",
        "servicio_sale_de_lote",
        "lote_abierto",
        "lote_solicitud",
        "lote_resuelto",
        "lista_espera_alta",
        "lista_espera_aviso",
    ]
    registrado_en: str = Field(description="Instante real del registro (ISO, UTC)")
    fecha_solicitud: str = Field(description="Fecha simulada de la demo en que ocurrió (`hoy`)")
    origen: Literal["chat", "api", "lote", "sistema"]
    estudiante_id: str | None = None
    servicio: ServicioEvento | None = None
    ocupacion: OcupacionEvento | None = None
    cita: CitaEvento | None = None
    desencuentro: DesencuentroEvento | None = None
    lote: LoteEvento | None = None
    espera: EsperaEvento | None = None
    umbral_pct: float | None = Field(default=None, description="Umbral de modo lote (solo en eventos de servicio_en_lote)")


class ActividadOut(BaseModel):
    epoca: str = Field(description="Cambia cuando se reinicia la demo")
    ultimo_id: int
    eventos: list[EventoActividad]
