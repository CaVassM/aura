"""Lista de espera: avisar a la persona si se libera un cupo que le sirve."""

from pydantic import BaseModel, Field

from .citas import OpcionOut


class EsperaOut(BaseModel):
    id: str
    estudiante_id: str
    estado: str = Field(description="`esperando`, `avisada` (ya se le avisó de un cupo) o `cancelada`")
    creada_en: str
    avisada_en: str | None = None
    motivo: str
    motivo_label: str
    servicio_ideal: str
    servicio_ideal_label: str
    distrito: str
    franjas: str = Field(description="Texto legible, p. ej. «miércoles 09:00–21:00»")
    canales: list[str]
    opcion: OpcionOut | None = Field(default=None, description="El cupo del que se le avisó (solo si `avisada`)")


class ListaEsperaOut(BaseModel):
    esperas: list[EsperaOut]
