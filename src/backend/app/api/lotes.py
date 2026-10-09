"""Modo lote: panorama para Coordinación."""

from fastapi import APIRouter, Depends

from ..deps import get_lotes
from ..schemas.lotes import LotesOut
from ..services.lote_service import LoteService

router = APIRouter(prefix="/api/coordinacion/lotes", tags=["coordinacion"])


@router.get("", response_model=LotesOut)
def panorama(servicio: LoteService = Depends(get_lotes)):
    """Servicios por utilización (con el umbral de modo lote), el lote abierto con su cuenta regresiva y el
    historial de lotes resueltos con la comparación genético vs orden de llegada."""
    return servicio.panorama()
