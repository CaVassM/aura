"""Inyección de dependencias (Depends): el AppState único y los servicios sobre él."""

from importlib.util import find_spec
from threading import Lock

from agente.config import ConfigAgente
from fastapi import Depends, Request

from .repositories.app_state import AppState
from .services.actividad_service import ActividadService
from .services.catalogo_service import CatalogoService
from .services.chat_service import ChatService
from .services.citas_service import CitasService
from .services.demo_service import DemoService
from .services.desencuentros_service import DesencuentrosService
from .services.errors import AgenteNoDisponibleError
from .services.lote_service import LoteService
from .services.reglas_service import ReglasService
from .services.resumen_service import ResumenService
from .services.servicios_service import ServiciosService


def get_estado(request: Request) -> AppState:
    return request.app.state.estado


def get_demo(estado: AppState = Depends(get_estado)) -> DemoService:
    return DemoService(estado)


def get_resumen(estado: AppState = Depends(get_estado)) -> ResumenService:
    return ResumenService(estado)


def get_servicios(estado: AppState = Depends(get_estado)) -> ServiciosService:
    return ServiciosService(estado)


def get_desencuentros(estado: AppState = Depends(get_estado)) -> DesencuentrosService:
    return DesencuentrosService(estado)


def get_reglas(estado: AppState = Depends(get_estado)) -> ReglasService:
    return ReglasService(estado)


def get_citas(estado: AppState = Depends(get_estado)) -> CitasService:
    return CitasService(estado)


def get_catalogo(estado: AppState = Depends(get_estado)) -> CatalogoService:
    return CatalogoService(estado)


_candado_agente = Lock()


def config_agente(request: Request) -> ConfigAgente:
    return getattr(request.app.state, "config_agente", None) or ConfigAgente.desde_entorno()


def dependencias_agente() -> bool:
    return all(find_spec(m) is not None for m in ("langchain", "langchain_ollama"))


def get_agente(request: Request):
    """El agente se crea al primer uso: el backend arranca aunque falten LangChain u Ollama."""
    with _candado_agente:
        if getattr(request.app.state, "agente", None) is None:
            if not dependencias_agente():
                raise AgenteNoDisponibleError(
                    "Faltan las dependencias del agente. Ejecuta: pip install -r requirements-agente.txt"
                )
            from agente.agente import AgenteAura

            request.app.state.agente = AgenteAura(config_agente(request))
        return request.app.state.agente


def get_chat(estado: AppState = Depends(get_estado), agente=Depends(get_agente)) -> ChatService:
    return ChatService(estado, agente)


def get_chat_sesiones(estado: AppState = Depends(get_estado)) -> ChatService:
    """Para historial y reinicio: no necesita (ni crea) el agente."""
    return ChatService(estado, None)


def get_actividad(estado: AppState = Depends(get_estado)) -> ActividadService:
    return ActividadService(estado)


def get_lotes(estado: AppState = Depends(get_estado)) -> LoteService:
    return LoteService(estado)
