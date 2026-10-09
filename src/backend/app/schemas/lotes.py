"""Modo lote: lo que muestra Coordinación y lo que ve el estudiante que espera."""

from typing import Literal

from pydantic import BaseModel, Field


class ServicioLoteOut(BaseModel):
    service_id: str
    nombre: str
    tipo: str
    tipo_label: str
    distrito: str
    pct: float = Field(description="Utilización: cupos reservados / cupos liberados × 100")
    reservados: int
    liberados: int
    en_lote: bool = Field(description="pct ≥ umbral: sus cupos solo se reparten por lote")


class SolicitudLoteOut(BaseModel):
    posicion: int
    estudiante_id: str
    entrada_en: str
    origen: str
    motivo: str
    motivo_label: str
    distrito: str
    grupo: str
    grupo_label: str


class MetricasLoteOut(BaseModel):
    objetivo: float = Field(description="Objetivo normalizado (menor es mejor)")
    asignados: int
    desencuentros: int
    espera_media: float
    espera_diurnos: float
    espera_nocturnos: float
    z: dict[str, float]


class AsignacionLoteOut(BaseModel):
    estudiante_id: str
    posicion_llegada: int
    orden_asignacion: int = Field(description="Lugar de prioridad que le dio el genético")
    servicio_nombre: str
    tipo_label: str
    distrito: str
    fecha: str
    hora_inicio: str
    hora_fin: str
    canal: str
    canal_label: str
    espera_dias: int
    es_alternativa: bool
    cita_id: str


class ResultadoLoteOut(BaseModel):
    asignados: int
    sin_cupo: int
    tiempo_s: float | None = None
    poblacion: int | None = None
    generaciones: int | None = None
    genetico: MetricasLoteOut | None = None
    llegada: MetricasLoteOut | None = Field(default=None, description="El mismo grupo asignado por orden de llegada")
    mejora_sobre_llegada: bool | None = None
    asignaciones: list[AsignacionLoteOut] = []
    sin_cupo_estudiantes: list[str] = []
    error: str | None = None


class LoteDetalleOut(BaseModel):
    id: int
    estado: Literal["abierto", "resolviendo", "resuelto"]
    abierto_en: str
    cierra_en: str
    cerrado_en: str | None = None
    solicitudes: list[SolicitudLoteOut]
    resultado: ResultadoLoteOut | None = None


class LotesOut(BaseModel):
    umbral_pct: float
    ventana_s: int
    tamano_maximo: int
    servidor_ahora: str = Field(description="Hora del servidor: sirve para calcular la cuenta regresiva sin depender del reloj del navegador")
    servicios: list[ServicioLoteOut] = Field(description="Todos los servicios, de mayor a menor utilización")
    abierto: LoteDetalleOut | None = None
    historial: list[LoteDetalleOut] = Field(description="Lotes ya resueltos, el más reciente primero")


class LoteEstadoOut(BaseModel):
    """El lote en el que espera una persona."""

    id: int
    estado: Literal["en_espera"]
    posicion: int
    solicitudes: int
    tamano_maximo: int
    cierra_en: str


class LoteEntradaOut(BaseModel):
    ok: bool
    lote: LoteEstadoOut


class AvisosOut(BaseModel):
    epoca: str
    ultimo_id: int
    avisos: list[dict]
