"""Actividad en vivo para Coordinación: registro de lo nuevo y flujo en tiempo real (SSE)."""

import asyncio
import json
import time

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import StreamingResponse

from ..deps import get_actividad, get_estado
from ..repositories.app_state import AppState
from ..schemas.actividad import ActividadOut
from ..services.actividad_service import ActividadService

router = APIRouter(prefix="/api/coordinacion/actividad", tags=["coordinacion"])

PING_CADA_S = 15
SONDEO_S = 0.3


@router.get("", response_model=ActividadOut)
def listar(
    desde: int = Query(0, ge=0, description="Devuelve solo los eventos con id mayor que este"),
    limite: int = Query(200, ge=1, le=1000),
    servicio: ActividadService = Depends(get_actividad),
):
    """Registro de lo **nuevo** (citas reservadas o canceladas y desencuentros hechos después de arrancar la
    demo), del más antiguo al más reciente. Las citas sembradas no aparecen."""
    return servicio.listar(desde, limite)


def _sse(evento: str, datos: dict, id_evento: int | None = None) -> str:
    cabecera = f"id: {id_evento}\n" if id_evento is not None else ""
    return f"{cabecera}event: {evento}\ndata: {json.dumps(datos, ensure_ascii=False)}\n\n"


async def flujo_actividad(estado: AppState, desde: int, desconectado=None, ping_cada_s: float = PING_CADA_S):
    """Genera el texto del flujo SSE. `desconectado` es una corrutina que dice si el cliente se fue."""
    repo = estado.actividad
    epoca = repo.epoca
    reinicio = desde > repo.ultimo_id  # el cliente vio otra ejecución (el backend o la demo se reiniciaron)
    ultimo = 0 if reinicio else desde
    yield "retry: 2000\n\n"
    yield _sse("inicio", {"epoca": epoca, "ultimo_id": repo.ultimo_id, "reinicio": reinicio})
    ultimo_ping = time.monotonic()
    while True:
        if desconectado is not None and await desconectado():
            return
        repo = estado.actividad  # al reiniciar la demo se reemplaza el registro
        if repo.epoca != epoca:
            epoca, ultimo = repo.epoca, 0
            yield _sse("reinicio", {"epoca": epoca})
        nuevos = repo.desde(ultimo)
        for evento in nuevos:
            ultimo = evento["id"]
            yield _sse("actividad", evento, evento["id"])
            ultimo_ping = time.monotonic()
        if not nuevos and time.monotonic() - ultimo_ping >= ping_cada_s:
            yield ": ping\n\n"  # mantiene viva la conexión a través de proxies
            ultimo_ping = time.monotonic()
        await asyncio.sleep(SONDEO_S)


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
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )
