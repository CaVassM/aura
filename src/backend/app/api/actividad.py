"""Actividad en vivo para Coordinación: registro de lo nuevo y flujo en tiempo real (SSE)."""

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse

from ..deps import get_actividad, get_estado
from ..repositories.app_state import AppState
from ..schemas.actividad import ActividadOut
from ..services.actividad_service import ActividadService
from .sse import CABECERAS, PING_CADA_S, flujo

router = APIRouter(prefix="/api/coordinacion/actividad", tags=["coordinacion"])


@router.get("", response_model=ActividadOut)
def listar(
    desde: int = Query(0, ge=0, description="Devuelve solo los eventos con id mayor que este"),
    limite: int = Query(200, ge=1, le=1000),
    servicio: ActividadService = Depends(get_actividad),
):
    """Registro de lo **nuevo** (citas reservadas o canceladas y desencuentros hechos después de arrancar la
    demo), del más antiguo al más reciente. Las citas sembradas no aparecen."""
    return servicio.listar(desde, limite)


async def flujo_actividad(estado: AppState, desde: int, desconectado=None, ping_cada_s: float = PING_CADA_S):
    """Flujo SSE de la actividad en vivo (ver `app.api.sse.flujo`)."""
    async for trozo in flujo(lambda: estado.actividad, desde, "actividad", desconectado, ping_cada_s):
        yield trozo


@router.get("/stream")
async def stream(
    request: Request,
    desde: int = Query(0, ge=0, description="Último id que el cliente ya tiene"),
    last_event_id: str | None = Header(default=None),
    estado: AppState = Depends(get_estado),
):
    """Flujo `text/event-stream`: un evento `actividad` por cada cita reservada o cancelada y por cada
    desencuentro, apenas ocurren. Al conectar manda `inicio` ({epoca, ultimo_id, reinicio}); si se reinicia
    la demo manda `reinicio`. `EventSource` reconecta solo y reenvía `Last-Event-ID`."""
    previo = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0
    return StreamingResponse(
        flujo_actividad(estado, max(desde, previo), request.is_disconnected),
        media_type="text/event-stream",
        headers=CABECERAS,
    )
