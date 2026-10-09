"""Registro de actividad en vivo: arma los eventos que ve Coordinación en tiempo real."""

from ..models import Cita
from ..repositories.app_state import AppState
from .etiquetas import Etiquetas
from .ocupacion import embudo_por_servicio, nivel, porcentaje


class ActividadService:
    def __init__(self, estado: AppState):
        self._estado = estado
        self._etiquetas = Etiquetas(estado.tablas)

    # --- escritura (la llaman CitasService y el chat) ---

    def cita_reservada(self, cita: Cita, comprobante: dict, origen: str) -> dict:
        return self._cita("cita_reservada", cita, comprobante, origen, delta=-1)

    def cita_cancelada(self, cita: Cita, origen: str) -> dict:
        return self._cita("cita_cancelada", cita, None, origen, delta=+1)

    def desencuentro(self, fila: dict, origen: str) -> dict:
        e = self._etiquetas
        franjas = "; ".join(
            f"{e.dia_largo(f['dia_semana'])} {f['desde']}–{f['hasta']}" for f in fila["franjas"]
        )
        return self._estado.actividad.agregar(
            "desencuentro",
            {
                **self._base(origen, fila["estudiante_id"]),
                "desencuentro": {
                    "registro_id": fila["registro_id"],
                    "motivo": fila["motivo"],
                    "motivo_label": e.motivo(fila["motivo"]),
                    "servicio_ideal": fila["servicio_ideal"],
                    "servicio_ideal_label": e.tipo(fila["servicio_ideal"]),
                    "distrito": fila["distrito"],
                    "grupo": fila["grupo"],
                    "grupo_label": e.grupo(fila["grupo"]),
                    "franjas": franjas,
                    "canales": list(fila["canales_aceptables"]),
                },
            },
        )

    # --- lectura ---

    def listar(self, desde: int = 0, limite: int = 200) -> dict:
        repo = self._estado.actividad
        return {"epoca": repo.epoca, "ultimo_id": repo.ultimo_id, "eventos": repo.desde(desde, limite)}

    # --- internos ---

    def _base(self, origen: str, estudiante_id: str) -> dict:
        return {
            "fecha_solicitud": self._estado.hoy.isoformat(),
            "origen": origen,
            "estudiante_id": estudiante_id,
        }

    def _cita(self, tipo: str, cita: Cita, comprobante: dict | None, origen: str, delta: int) -> dict:
        servicio = self._estado.motor.servicio(cita.service_id)
        datos = {
            **self._base(origen, cita.estudiante_id),
            "servicio": {
                "service_id": cita.service_id,
                "nombre": cita.servicio_nombre,
                "tipo": cita.tipo,
                "tipo_label": cita.tipo_label,
                "distrito": servicio["distrito"] if servicio else cita.distrito,
            },
            "ocupacion": self._ocupacion(cita.service_id, delta),
            "cita": {
                "cita_id": cita.id,
                "fecha": cita.fecha,
                "hora_inicio": cita.hora_inicio,
                "hora_fin": cita.hora_fin,
                "canal": cita.canal,
                "canal_label": self._etiquetas.canal(cita.canal),
                "dias_espera": (comprobante or {}).get("dias_espera"),
                "es_alternativa": bool((comprobante or {}).get("es_alternativa", False)),
            },
        }
        return self._estado.actividad.agregar(tipo, datos)

    def _ocupacion(self, service_id: str, delta: int) -> dict | None:
        """Ocupación del servicio ya con el evento aplicado; `delta` es lo que cambió (-1 al reservar)."""
        _, _, por_servicio = embudo_por_servicio(self._estado)
        fila = por_servicio.get(service_id)
        if not fila:
            return None
        ahora = porcentaje(fila["reservados"], fila["liberados"])
        antes = porcentaje(fila["reservados"] + delta, fila["liberados"])
        return {
            "pct": ahora,
            "antes_pct": antes,
            "reservados": fila["reservados"],
            "liberados": fila["liberados"],
            "nivel": nivel(self._estado, ahora),
        }
