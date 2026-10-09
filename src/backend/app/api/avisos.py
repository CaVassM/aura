"""Avisos para el estudiante (p. ej. «tu lote se resolvió»): consulta y flujo en tiempo real (SSE)."""

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse

from ..deps import get_estado
from ..repositories.app_state import AppState
from ..repositories.avisos_repository import AvisosDe
from ..schemas.lotes import AvisosOut
from .sse import CABECERAS, flujo

router = APIRouter(prefix="/api/estudiantes/{estudiante_id}/avisos", tags=["estudiante"])


@router.get("", response_model=AvisosOut)
def listar(estudiante_id: str, desde: int = Query(0, ge=0), estado: AppState = Depends(get_estado)):
    """Avisos de la persona con id mayor que `desde`, del más antiguo al más reciente."""
    vista = AvisosDe(estado.avisos, estudiante_id)
    return {"epoca": vista.epoca, "ultimo_id": vista.ultimo_id, "avisos": vista.desde(desde)}


async def flujo_avisos(estado: AppState, estudiante_id: str, desde: int, desconectado=None, ping_cada_s: float = 15):
    async for trozo in flujo(lambda: AvisosDe(estado.avisos, estudiante_id), desde, "aviso", desconectado, ping_cada_s):
        yield trozo


@router.get("/stream")
async def stream(
    estudiante_id: str,
    request: Request,
    desde: int = Query(0, ge=0),
    last_event_id: str | None = Header(default=None),
    estado: AppState = Depends(get_estado),
):
    """Flujo `text/event-stream` de los avisos de esta persona (mismo formato que el de actividad, con
    `event: aviso`): `lote_en_espera`, `lote_asignada`, `lote_sin_cupo` y `lote_error`."""
    previo = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0
    return StreamingResponse(
        flujo_avisos(estado, estudiante_id, max(desde, previo), request.is_disconnected),
        media_type="text/event-stream",
        headers=CABECERAS,
    )
