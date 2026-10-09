"""Chat con el agente conversacional AURA (estudiante)."""

from fastapi import APIRouter, Depends, Query, Request

from ..deps import config_agente, dependencias_agente, get_chat, get_chat_sesiones
from ..schemas.chat import ChatEstadoOut, ChatIn, ChatOut, HistorialOut
from ..services.chat_service import ChatService, estado_ollama

router = APIRouter(prefix="/api/chat", tags=["estudiante"])


@router.post("", response_model=ChatOut)
def conversar(cuerpo: ChatIn, servicio: ChatService = Depends(get_chat)):
    """Un mensaje de la persona. El agente responde y, si hace falta, propone, reserva o cancela citas.

    Tarda de segundos a minutos según el modelo local de Ollama.
    """
    return servicio.conversar(
        cuerpo.mensaje, cuerpo.estudiante_id, cuerpo.session_id, cuerpo.distrito, cuerpo.grupo
    )


@router.get("/estado", response_model=ChatEstadoOut)
def estado(request: Request):
    """¿Están las dependencias, responde Ollama y está descargado el modelo?"""
    return estado_ollama(config_agente(request), dependencias_agente())


@router.get("/{session_id}", response_model=HistorialOut)
def historial(session_id: str, estudiante_id: str = Query(...), servicio: ChatService = Depends(get_chat_sesiones)):
    return servicio.historial(session_id, estudiante_id)


@router.delete("/{session_id}")
def reiniciar(session_id: str, estudiante_id: str = Query(...), servicio: ChatService = Depends(get_chat_sesiones)):
    """Borra la conversación (no cancela citas ya reservadas)."""
    return servicio.reiniciar(session_id, estudiante_id)
