"""Citas del estudiante: proponer opciones, reservar, listar y cancelar."""

from fastapi import APIRouter, Depends, Query

from ..deps import get_citas, get_lotes
from ..schemas.citas import CitaOut, PropuestaOut, ReservaIn, SolicitudIn, cita_out
from ..schemas.lotes import LoteEntradaOut
from ..services.citas_service import CitasService
from ..services.lote_service import LoteService

router = APIRouter(prefix="/api/appointments", tags=["estudiante"])


@router.post("/proposals", response_model=PropuestaOut)
def proponer(
    cuerpo: SolicitudIn,
    k: int = Query(3, ge=1, le=20),
    servicio: CitasService = Depends(get_citas),
):
    """Opciones compatibles con las preferencias; no reserva ni retiene cupos."""
    return servicio.proponer(cuerpo.model_dump(exclude_none=True), k)


@router.post("/lote", response_model=LoteEntradaOut, status_code=201)
def entrar_a_lote(cuerpo: SolicitudIn, servicio: LoteService = Depends(get_lotes)):
    """Pone la solicitud en el lote abierto (lo abre si no hay). Solo vale cuando `proposals` devolvió
    `motivo_vacio: "servicios_en_lote"`: los servicios compatibles están en modo lote y se asignan en conjunto."""
    datos = cuerpo.model_dump(exclude_none=True)
    return servicio.entrar(datos["estudiante_id"], datos, origen="api")


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
