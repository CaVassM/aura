"""Lista de espera del estudiante: anotarse cuando no hay cupo y consultar o salir de ella."""

from fastapi import APIRouter, Depends

from ..deps import get_estado
from ..repositories.app_state import AppState
from ..schemas.citas import SolicitudIn
from ..schemas.lista_espera import EsperaOut, ListaEsperaOut
from ..services.lista_espera_service import ListaEsperaService

router = APIRouter(tags=["estudiante"])


@router.post("/api/appointments/lista-espera", response_model=EsperaOut, status_code=201)
def anotarse(cuerpo: SolicitudIn, estado: AppState = Depends(get_estado)):
    """Anota a la persona con las preferencias que no tuvieron cupo. Cuando se libere uno que le sirva (al cancelarse una
    cita) le llega un aviso en `/api/estudiantes/{id}/avisos/stream` (`tipo: cupo_disponible`)."""
    datos = cuerpo.model_dump(exclude_none=True)
    return ListaEsperaService(estado).anotar(datos["estudiante_id"], datos, origen="api")


@router.get("/api/estudiantes/{estudiante_id}/lista-espera", response_model=ListaEsperaOut)
def listar(estudiante_id: str, estado: AppState = Depends(get_estado)):
    return {"esperas": ListaEsperaService(estado).listar(estudiante_id)}


@router.delete("/api/estudiantes/{estudiante_id}/lista-espera/{espera_id}", response_model=EsperaOut)
def salir(estudiante_id: str, espera_id: str, estado: AppState = Depends(get_estado)):
    return ListaEsperaService(estado).cancelar(estudiante_id, espera_id)
