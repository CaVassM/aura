"""Vida académica simulada del estudiante: cursos, calificaciones y calendario (D7)."""

from fastapi import APIRouter, Depends

from ..deps import get_academico
from ..schemas.academico import CalendarioOut, CalificacionesOut, CursosOut
from ..services.academico_service import AcademicoService

router = APIRouter(prefix="/api/estudiantes/{estudiante_id}/academico", tags=["estudiante"])


@router.get("/cursos", response_model=CursosOut)
def cursos(estudiante_id: str, servicio: AcademicoService = Depends(get_academico)):
    """Cursos del período con horario, docente, asistencia y próxima evaluación."""
    return servicio.cursos(estudiante_id)


@router.get("/calificaciones", response_model=CalificacionesOut)
def calificaciones(estudiante_id: str, servicio: AcademicoService = Depends(get_academico)):
    """Evaluaciones y notas por curso, promedio del período y nota que falta para aprobar."""
    return servicio.calificaciones(estudiante_id)


@router.get("/calendario", response_model=CalendarioOut)
def calendario(estudiante_id: str, servicio: AcademicoService = Depends(get_academico)):
    """Calendario D7 del período (según su institución y distrito) con sus clases y evaluaciones."""
    return servicio.calendario(estudiante_id)
