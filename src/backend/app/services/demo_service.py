"""Estado de la demo y reinicio."""

from ..repositories.app_state import AppState
from .ocupacion import agenda, agenda_abierta, rango_semana
from .siembra_service import crear_estado_sembrado


class DemoService:
    def __init__(self, estado: AppState):
        self._estado = estado

    def estado(self) -> dict:
        e = self._estado.escenario
        inicio, fin = rango_semana(e["hoy"])
        agenda_desde, agenda_hasta = agenda(self._estado)
        abierta_desde, abierta_hasta = agenda_abierta(self._estado)
        return {
            "hoy": e["hoy"],
            "semana_inicio": inicio,
            "semana_fin": fin,
            "agenda_inicio": agenda_desde,
            "agenda_fin": agenda_hasta,
            "agenda_abierta_inicio": abierta_desde,
            "agenda_abierta_fin": abierta_hasta,
            "escenario": e["nombre"],
            "etiqueta": e["etiqueta"],
            "semilla": e["semilla"],
            "factor_demanda": e["factor"],
            "proporcion_vespertino_trabaja": e["proporcion_vespertino_trabaja"],
            "umbrales_nivel": self._estado.parametros["coordinacion"]["nivel_ocupacion"],
        }

    def reiniciar(self) -> dict:
        """Reconstruye la agenda y vuelve a sembrar; descarta citas y desencuentros nuevos."""
        e = self._estado.escenario
        nuevo = crear_estado_sembrado(self._estado.settings, e["nombre"], e["semilla"])
        self._estado.reemplazar_por(nuevo)
        return self.estado()
