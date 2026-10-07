"""Catálogo de servicios de apoyo y sus horarios libres (vista del estudiante)."""

from ..repositories.app_state import AppState
from .errors import NotFoundError
from .etiquetas import Etiquetas


class CatalogoService:
    def __init__(self, estado: AppState):
        self._motor = estado.motor
        self._etiquetas = Etiquetas(estado.tablas)

    def servicios(self) -> list[dict]:
        return [
            {**s, "tipo_label": self._etiquetas.tipo(s["tipo"])} for s in self._motor.servicios()
        ]

    def cupos_libres(self, service_id: str) -> list[dict]:
        if self._motor.servicio(service_id) is None:
            raise NotFoundError(service_id)
        return self._motor.cupos_libres(service_id)
