"""Citas y catálogo (vista del estudiante)."""

from functools import lru_cache

from aura.herramientas.configuracion import cargar_yaml
from pydantic import BaseModel, Field

from ..services.etiquetas import Etiquetas


@lru_cache(maxsize=1)
def _etiquetas() -> Etiquetas:
    return Etiquetas(cargar_yaml("tablas.yaml"))


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
    solo_servicio_ideal: bool = Field(
        default=False, description="La persona no acepta otro servicio que el ideal para su motivo (sin alternativos)"
    )
    service_id_preferido: str | None = Field(
        default=None,
        description="Servicio que la persona pidió por nombre o id (p. ej. «Brújula»): sus opciones van primero",
    )


class ReservaIn(BaseModel):
    estudiante_id: str
    opcion_id: str = Field(description="`<cupo_id>|<canal>`, p. ej. C0000123|digital")
    servicio_ideal: str | None = Field(
        default=None,
        description="Opcional: `servicio_ideal` de la propuesta; permite contar la demanda desviada",
    )
    reemplazar: bool = Field(
        default=False,
        description="R7: si ya tiene una cita activa de ese tipo de servicio, la cancela al reservar esta (una sola operación)",
    )


class OpcionOut(BaseModel):
    """Una opción de la propuesta: un cupo concreto, o un servicio en modo lote (sin día ni hora: los decide el lote)."""

    opcion_id: str = Field(description="`<cupo_id>|<canal>` para un cupo; `LOTE|<service_id>` para un servicio en lote")
    tipo_opcion: str = Field(default="cupo", description="`cupo` o `lote`")
    service_id: str
    servicio_nombre: str
    tipo: str
    tipo_label: str
    distrito: str
    fecha: str | None = None
    dia_semana: str | None = None
    hora_inicio: str | None = None
    hora_fin: str | None = None
    canal: str | None = None
    canal_label: str | None = None
    dias_espera: int | None = None
    es_alternativa: bool
    afinidad: float
    cupos_libres: int | None = Field(default=None, description="Solo `lote`: cupos libres compatibles del servicio")
    tiempo_respuesta_s: int | None = Field(default=None, description="Solo `lote`: segundos en que se resuelve el lote")
    mensaje: str | None = Field(default=None, description="Solo `lote`: texto listo para mostrar")


class PropuestaOut(BaseModel):
    opciones: list[OpcionOut] = Field(description="Máximo 3; el servicio ideal (o el pedido por nombre) primero")
    servicio_ideal: str | None = None
    motivo_vacio: str | None = None
    mensaje: str | None = Field(
        default=None,
        description="Texto del backend para los casos especiales (sin cupos, servicio en lote, servicio pedido sin cupo)",
    )
    preferido: dict | None = Field(
        default=None,
        description="Si se pidió un servicio por nombre: si se encontró, si tiene cupo y, si no, su fecha más cercana y la "
        "mejor opción del mismo tipo en otro servicio",
    )
    sugerencia: str | None = None


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
    tipo: str
    tipo_label: str
    distrito: str
    hora_fin: str
    slot: SlotOut
    canal: str
    estado: str
    aviso_canal: str = Field(default="", description="Línea de la confirmación según el canal (enlace, llamada o lugar)")


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
        tipo=cita.tipo,
        tipo_label=cita.tipo_label,
        distrito=cita.distrito,
        hora_fin=cita.hora_fin,
        slot=SlotOut(
            id=cita.cupo_id,
            service_id=cita.service_id,
            fecha_iso=f"{cita.fecha}T{cita.hora_inicio}:00",
            disponible=False,
            canales=[cita.canal],
        ),
        canal=cita.canal,
        estado=cita.estado,
        aviso_canal=_etiquetas().confirmacion_canal(cita.canal, cita.servicio_nombre, cita.distrito),
    )
