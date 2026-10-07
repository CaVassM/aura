"""Citas del estudiante: proponer opciones, reservar, listar y cancelar."""

from fastapi import APIRouter, Depends, Query

from ..deps import get_citas
from ..schemas.citas import CitaOut, PropuestaOut, ReservaIn, SolicitudIn, cita_out
from ..services.citas_service import CitasService

router = APIRouter(prefix="/api/appointments", tags=["estudiante"])


@router.post("/proposals", response_model=PropuestaOut)
def proponer(
    cuerpo: SolicitudIn,
    k: int = Query(3, ge=1, le=20),
    servicio: CitasService = Depends(get_citas),
):
    """Opciones compatibles con las preferencias; no reserva ni retiene cupos."""
    return servicio.proponer(cuerpo.model_dump(exclude_none=True), k)


@router.post("", response_model=CitaOut, status_code=201)
def reservar(cuerpo: ReservaIn, servicio: CitasService = Depends(get_citas)):
    return cita_out(servicio.reservar(cuerpo.estudiante_id, cuerpo.opcion_id, cuerpo.servicio_ideal))


@router.get("", response_model=list[CitaOut])
def listar(estudiante_id: str, servicio: CitasService = Depends(get_citas)):
    return [cita_out(c) for c in servicio.listar(estudiante_id)]


@router.delete("/{cita_id}", response_model=CitaOut)
def cancelar(
    cita_id: str,
    estudiante_id: str | None = None,
    servicio: CitasService = Depends(get_citas),
):
    return cita_out(servicio.cancelar(cita_id, estudiante_id))
