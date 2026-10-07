from fastapi import APIRouter, Depends, Query, Response

from ..deps import get_desencuentros
from ..schemas.desencuentros import DesencuentrosOut
from ..services.desencuentros_service import DesencuentrosService

router = APIRouter(prefix="/api/coordinacion", tags=["coordinacion"])


@router.get("/desencuentros", response_model=DesencuentrosOut)
def desencuentros(
    motivo: str | None = None,
    distrito: str | None = None,
    servicio_ideal: str | None = None,
    grupo: str | None = None,
    pagina: int = Query(1, ge=1),
    tamano: int = Query(8, ge=1, le=100),
    servicio: DesencuentrosService = Depends(get_desencuentros),
):
    return servicio.listar(motivo, distrito, servicio_ideal, grupo, pagina, tamano)


@router.get("/desencuentros.csv")
def desencuentros_csv(
    motivo: str | None = None,
    distrito: str | None = None,
    servicio_ideal: str | None = None,
    grupo: str | None = None,
    servicio: DesencuentrosService = Depends(get_desencuentros),
):
    contenido = servicio.csv(motivo, distrito, servicio_ideal, grupo)
    return Response(
        content="﻿" + contenido,  # BOM para que Excel lea las tildes
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="desencuentros.csv"'},
    )
