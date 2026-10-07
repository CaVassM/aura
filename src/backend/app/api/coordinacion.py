from datetime import date

from fastapi import APIRouter, Depends, Query

from ..deps import get_resumen, get_servicios
from ..schemas.coordinacion import ResumenOut, ServiciosGeoJSON
from ..schemas.desencuentros import ServicioDetalleOut
from ..services.resumen_service import ResumenService
from ..services.servicios_service import ServiciosService

router = APIRouter(prefix="/api/coordinacion", tags=["coordinacion"])

SEMANA = Query(None, description="Fecha YYYY-MM-DD: acota a su semana (Lun–Dom). Sin ella, toda la agenda abierta (hoy + 1 …)")


@router.get("/resumen", response_model=ResumenOut)
def resumen(semana: date | None = SEMANA, servicio: ResumenService = Depends(get_resumen)):
    return servicio.resumen(semana)


@router.get("/servicios", response_model=ServiciosGeoJSON)
def servicios(
    tipo: str | None = None,
    canal: str | None = None,
    solo_alta_demanda: bool = False,
    semana: date | None = SEMANA,
    servicio: ServiciosService = Depends(get_servicios),
):
    return servicio.geojson(tipo, canal, solo_alta_demanda, semana)


@router.get("/servicios/{service_id}", response_model=ServicioDetalleOut)
def detalle_servicio(
    service_id: str,
    semana: date | None = SEMANA,
    servicio: ServiciosService = Depends(get_servicios),
):
    return servicio.detalle(service_id, semana)
