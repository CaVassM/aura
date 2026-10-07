"""Catálogo de servicios y horarios libres (vista del estudiante)."""

from fastapi import APIRouter, Depends

from ..deps import get_catalogo
from ..schemas.citas import ServicioOut, SlotOut, slot_desde_cupo
from ..services.catalogo_service import CatalogoService

router = APIRouter(prefix="/api/services", tags=["estudiante"])


@router.get("", response_model=list[ServicioOut])
def listar(servicio: CatalogoService = Depends(get_catalogo)):
    return servicio.servicios()


@router.get("/{service_id}/slots", response_model=list[SlotOut])
def horarios(service_id: str, servicio: CatalogoService = Depends(get_catalogo)):
    return [slot_desde_cupo(c) for c in servicio.cupos_libres(service_id)]
