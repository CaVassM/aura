from fastapi import APIRouter, Depends

from ..deps import get_reglas
from ..schemas.reglas import ReglasOut
from ..services.reglas_service import ReglasService

router = APIRouter(prefix="/api/coordinacion", tags=["coordinacion"])


@router.get("/reglas", response_model=ReglasOut)
def reglas(servicio: ReglasService = Depends(get_reglas)):
    return servicio.reglas()
