"""Citas y catálogo (vista del estudiante)."""

from pydantic import BaseModel, Field


class FranjaIn(BaseModel):
    dia: str = Field(examples=["Tue"])
    desde: str = Field(examples=["09:00"])
    hasta: str = Field(examples=["18:00"])


class SolicitudIn(BaseModel):
    """Preferencias de cita; mismo contenido que el contrato de herramientas del agente."""

    estudiante_id: str
    motivo: str = Field(examples=["academic_pressure"])
    distrito: str = Field(examples=["DIST_GAIA"])
    franjas: list[FranjaIn] = Field(min_length=1)
    canales_aceptables: list[str] = Field(min_length=1, examples=[["digital", "phone"]])
    grupo: str = Field(default="diurno", pattern="^(diurno|nocturno)$")
    fecha_solicitud: str | None = None


class ReservaIn(BaseModel):
    estudiante_id: str
    opcion_id: str = Field(description="`<cupo_id>|<canal>`, p. ej. C0000123|digital")
    servicio_ideal: str | None = Field(
        default=None,
        description="Opcional: `servicio_ideal` de la propuesta; permite contar la demanda desviada",
    )


class OpcionOut(BaseModel):
    opcion_id: str
    service_id: str
    servicio_nombre: str
    tipo: str
    tipo_label: str
    distrito: str
    fecha: str
    hora_inicio: str
    hora_fin: str
    canal: str
    dias_espera: int
    es_alternativa: bool
    afinidad: float


class PropuestaOut(BaseModel):
    opciones: list[OpcionOut]
    servicio_ideal: str | None = None
    motivo_vacio: str | None = None


class ServicioOut(BaseModel):
    service_id: str
    nombre: str
    tipo: str
    tipo_label: str
    distrito: str
    canales: list[str]
    capacidad_semanal: int


class SlotOut(BaseModel):
    id: str = Field(description="Id del cupo; la opción a reservar es `<id>|<canal>`")
    service_id: str
    fecha_iso: str
    disponible: bool = True
    canales: list[str] = []


class CitaOut(BaseModel):
    id: str
    estudiante_id: str
    service_id: str
    servicio_nombre: str
    tipo_label: str
    slot: SlotOut
    canal: str
    estado: str


def slot_desde_cupo(cupo: dict) -> SlotOut:
    return SlotOut(
        id=cupo["cupo_id"],
        service_id=cupo["service_id"],
        fecha_iso=f"{cupo['fecha']}T{cupo['hora_inicio']}:00",
        canales=cupo["canales"],
    )


def cita_out(cita) -> CitaOut:
    return CitaOut(
        id=cita.id,
        estudiante_id=cita.estudiante_id,
        service_id=cita.service_id,
        servicio_nombre=cita.servicio_nombre,
        tipo_label=cita.tipo_label,
        slot=SlotOut(
            id=cita.cupo_id,
            service_id=cita.service_id,
            fecha_iso=f"{cita.fecha}T{cita.hora_inicio}:00",
            disponible=False,
            canales=[cita.canal],
        ),
        canal=cita.canal,
        estado=cita.estado,
    )
