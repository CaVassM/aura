"""Servicios de la red: propiedades, ocupación semanal y GeoJSON para el mapa."""

from collections import defaultdict
from datetime import date

from ..repositories.app_state import AppState
from .demanda_service import DemandaService
from .desencuentros_service import DesencuentrosService
from .errors import NotFoundError
from .etiquetas import Etiquetas
from .ocupacion import nivel, ocupacion_por_servicio, porcentaje


class ServiciosService:
    def __init__(self, estado: AppState):
        self._estado = estado
        self._etiquetas = Etiquetas(estado.tablas)

    def _propiedades(self, semana: date | None) -> list[tuple[dict, dict]]:
        """(feature de D6, propiedades de la API) de cada servicio, en el orden de D6."""
        estado, et = self._estado, self._etiquetas
        _, _, ocupacion = ocupacion_por_servicio(estado, semana)
        motor = {s["service_id"]: s for s in estado.motor.servicios()}
        resultado = []
        for feature in estado.geo:
            s = motor[feature["service_id"]]
            d6 = feature["properties"]
            fila = ocupacion.get(s["service_id"], {"liberados": 0, "ocupados": 0})
            pct = porcentaje(fila["ocupados"], fila["liberados"])
            nivel_ = nivel(estado, pct)
            propiedades = {
                "service_id": s["service_id"],
                "nombre": s["nombre"],
                "tipo": s["tipo"],
                "tipo_label": et.tipo(s["tipo"]),
                "distrito": s["distrito"],
                "direccion": d6.get("address"),
                "horario_texto": et.horario_texto(s["horario"]),
                "horario": et.horario_estructurado(s["horario"]),
                "canales": s["canales"],
                "canales_label": [et.canal(c) for c in s["canales"]],
                "capacidad_semanal": s["capacidad_semanal"],
                "cupos_liberados": fila["liberados"],
                "cupos_ocupados": fila["ocupados"],
                "ocupacion_pct": pct,
                "nivel": nivel_,
                "alta_demanda": nivel_ == "alta",
                "eligibility": d6.get("eligibility"),
                "referral_information": d6.get("referral_information"),
                "pos": feature["pos"],
            }
            resultado.append((feature, propiedades))
        return resultado

    def geojson(self, tipo=None, canal=None, solo_alta_demanda=False, semana=None) -> dict:
        features = [
            {
                "type": "Feature",
                "id": p["service_id"],
                "geometry": feature["geometry"],
                "properties": p,
            }
            for feature, p in self._propiedades(semana)
            if (tipo is None or p["tipo"] == tipo)
            and (canal is None or canal in p["canales"])
            and (not solo_alta_demanda or p["alta_demanda"])
        ]
        return {"type": "FeatureCollection", "features": features}

    def detalle(self, service_id: str, semana: date | None = None) -> dict:
        encontrado = next(
            (p for _, p in self._propiedades(semana) if p["service_id"] == service_id), None
        )
        if encontrado is None:
            raise NotFoundError(service_id)
        por_dia: dict[str, dict[str, int]] = defaultdict(lambda: {"liberados": 0, "ocupados": 0})
        for cupo in self._estado.motor.cupos_liberados(service_id):
            por_dia[cupo["fecha"]]["liberados"] += 1
            por_dia[cupo["fecha"]]["ocupados"] += cupo["ocupado"]
        demanda = DemandaService(self._estado)
        citas = self._estado.motor.citas()
        del_servicio = [c for c in citas if c["service_id"] == service_id]
        return {
            "servicio": encontrado,
            "demanda_del_tipo": next(
                d for d in demanda.por_tipo(citas) if d["ideal"] == encontrado["tipo"]
            ),
            "recibidos_como_alternativa": demanda.recibidos_como_alternativa(
                del_servicio, encontrado["tipo"]
            ),
            "cupos_por_dia": [
                {
                    "fecha": fecha,
                    "dia": self._etiquetas.dia(date.fromisoformat(fecha).weekday()),
                    "abierto": fecha > self._estado.hoy.isoformat(),
                    **conteo,
                }
                for fecha, conteo in sorted(por_dia.items())
            ],
            "desencuentros_recientes": DesencuentrosService(self._estado).recientes(
                encontrado["tipo"], encontrado["distrito"]
            ),
        }
