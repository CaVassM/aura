from fastapi import APIRouter

from ..schemas.comun import Salud

router = APIRouter(prefix="/api", tags=["salud"])


@router.get("/salud", response_model=Salud)
def salud() -> Salud:
    return Salud()
