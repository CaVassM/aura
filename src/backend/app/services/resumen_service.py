"""Resumen de la red para el panel de coordinación."""

from datetime import date

from ..repositories.app_state import AppState
from .demanda_service import DemandaService
from .etiquetas import Etiquetas
from .ocupacion import (
    nivel,
    ocupacion_por_servicio,
    porcentaje,
    rango_pedidos,
    rango_semana,
)


class ResumenService:
    def __init__(self, estado: AppState):
        self._estado = estado
        self._etiquetas = Etiquetas(estado.tablas)

    def _citas(self, semana: date | None) -> tuple[list[dict], tuple[date, date]]:
        """Citas sembradas (todas, o las solicitadas en la semana) y el rango que cubren."""
        rango = rango_semana(semana) if semana else rango_pedidos(self._estado)
        desde, hasta = (d.isoformat() for d in rango)
        citas = [c for c in self._estado.motor.citas() if desde <= c["fecha_solicitud"] <= hasta]
        return citas, rango

    def resumen(self, semana: date | None = None) -> dict:
        estado = self._estado
        inicio, fin, por_servicio = ocupacion_por_servicio(estado, semana)
        citas, (pedidos_desde, pedidos_hasta) = self._citas(semana)
        esperas = [c["dias_espera"] for c in citas]  # fecha_cupo − fecha_solicitud, como en D2
        liberados = sum(f["liberados"] for f in por_servicio.values())
        ocupados = sum(f["ocupados"] for f in por_servicio.values())
        servicios = []
        for s in estado.motor.servicios():
            fila = por_servicio.get(s["service_id"], {"liberados": 0, "ocupados": 0})
            pct = porcentaje(fila["ocupados"], fila["liberados"])
            servicios.append(
                {
                    "service_id": s["service_id"],
                    "nombre": s["nombre"],
                    "tipo": s["tipo"],
                    "tipo_label": self._etiquetas.tipo(s["tipo"]),
                    "ocupacion_pct": pct,
                    "nivel": nivel(estado, pct),
                    "cupos_liberados": fila["liberados"],
                    "cupos_ocupados": fila["ocupados"],
                }
            )
        demanda = DemandaService(estado).por_tipo(citas)
        return {
            "agenda_abierta": {"desde": inicio, "hasta": fin},
            "pedidos": {"desde": pedidos_desde, "hasta": pedidos_hasta},
            "kpis": {
                "citas_agendadas": len(citas),
                "espera_media_dias": round(sum(esperas) / len(esperas), 1) if esperas else 0.0,
                "espera_linea_base_dias": round(estado.espera_linea_base_dias, 2),
                "cupos_liberados": liberados,
                "cupos_ocupados": ocupados,
                "ocupacion_pct": porcentaje(ocupados, liberados),
                "desencuentros": len(estado.desencuentros),
                "atendidos_alternativa": sum(d["atendidos_con_alternativa"] for d in demanda),
            },
            "demanda_por_tipo": demanda,
            "servicios": servicios,
        }
