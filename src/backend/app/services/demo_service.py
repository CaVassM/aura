"""Estado de la demo y reinicio."""

from ..repositories.app_state import AppState
from .ocupacion import agenda, agenda_abierta, rango_pedidos, rango_semana
from .siembra_service import crear_estado_sembrado


class DemoService:
    def __init__(self, estado: AppState):
        self._estado = estado

    def estado(self) -> dict:
        e = self._estado.escenario
        inicio, fin = rango_semana(e["hoy"])
        agenda_desde, agenda_hasta = agenda(self._estado)
        abierta_desde, abierta_hasta = agenda_abierta(self._estado)
        pedidos_desde, pedidos_hasta = rango_pedidos(self._estado)
        p = self._estado.parametros
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
            "pedidos_desde": pedidos_desde,
            "pedidos_hasta": pedidos_hasta,
            "agenda_abierta_semanas": int(p["horizonte_semanas"]),
            "ocupacion_inicial_pct": round(100 * float(p["ocupacion_inicial"]), 1),
            "fraccion_liberada_pct": round(100 * e["fraccion_liberada"], 1),
            "espera_linea_base_dias": round(self._estado.espera_linea_base_dias, 2),
            "umbrales_nivel": self._estado.parametros["coordinacion"]["nivel_ocupacion"],
        }

    def reiniciar(self) -> dict:
        """Reconstruye la agenda y vuelve a sembrar; descarta citas y desencuentros nuevos."""
        e = self._estado.escenario
        nuevo = crear_estado_sembrado(self._estado.settings, e["nombre"], e["semilla"])
        self._estado.reemplazar_por(nuevo)
        return self.estado()
