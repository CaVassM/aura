from fastapi import APIRouter, Depends

from ..deps import get_demo
from ..schemas.demo import EstadoDemo
from ..services.demo_service import DemoService

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.get("/estado", response_model=EstadoDemo)
def estado(servicio: DemoService = Depends(get_demo)):
    return servicio.estado()


@router.post("/reiniciar", response_model=EstadoDemo)
def reiniciar(servicio: DemoService = Depends(get_demo)):
    """Reconstruye el estado y vuelve a sembrar la demo."""
    return servicio.reiniciar()
