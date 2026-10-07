"""Inyección de dependencias (Depends): el AppState único y los servicios sobre él."""

from fastapi import Depends, Request

from .repositories.app_state import AppState
from .services.catalogo_service import CatalogoService
from .services.citas_service import CitasService
from .services.demo_service import DemoService
from .services.desencuentros_service import DesencuentrosService
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
