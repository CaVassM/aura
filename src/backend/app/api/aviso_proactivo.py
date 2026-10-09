"""Aviso proactivo del campus («un espacio para ti»): si se le muestra a la persona y cómo darlo de baja."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..deps import get_estado
from ..repositories.app_state import AppState
from ..schemas.academico import SemanaEvaluacionOut
from ..services.aviso_proactivo_service import AvisoProactivoService

router = APIRouter(prefix="/api/estudiantes/{estudiante_id}/aviso-proactivo", tags=["estudiante"])


class SenalOut(BaseModel):
    id: str
    nombre: str
    cumple: bool


class AvisoProactivoOut(BaseModel):
    mostrar: bool = Field(description="Mostrar la tarjeta: elegible, en semana de evaluaciones y sin haberla dado de baja")
    elegible: bool
    descartado: bool = Field(description="La persona lo dio de baja")
    puntaje: int
    minimo: int
    senales: list[SenalOut] = Field(description="Para verificar la regla; la vista del estudiante no las muestra")
    semana: SemanaEvaluacionOut | None = Field(description="Semana de evaluaciones en curso (D7)")


@router.get("", response_model=AvisoProactivoOut)
def ver(estudiante_id: str, estado: AppState = Depends(get_estado)):
    return AvisoProactivoService(estado).estado(estudiante_id)


@router.post("/baja", response_model=AvisoProactivoOut)
def dar_de_baja(estudiante_id: str, estado: AppState = Depends(get_estado)):
    """La persona no quiere ver este aviso. Se recuerda hasta reiniciar la demo."""
    return AvisoProactivoService(estado).dar_de_baja(estudiante_id)


@router.delete("/baja", response_model=AvisoProactivoOut)
def reactivar(estudiante_id: str, estado: AppState = Depends(get_estado)):
    return AvisoProactivoService(estado).reactivar(estudiante_id)
