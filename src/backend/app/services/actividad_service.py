"""Registro de actividad en vivo: arma los eventos que ve Coordinación en tiempo real."""

from ..models import Cita
from ..repositories.app_state import AppState
from .etiquetas import Etiquetas
from .ocupacion import embudo_por_servicio, en_lote, nivel, porcentaje, umbral_lote


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

    def lista_espera(self, tipo: str, entrada: dict, origen: str) -> dict:
        """`lista_espera_alta` (alguien quedó esperando un cupo) y `lista_espera_aviso` (se le avisó de uno)."""
        opcion = entrada.get("opcion") if tipo == "lista_espera_aviso" else None
        return self._estado.actividad.agregar(
            tipo,
            {
                **self._base(origen, entrada["estudiante_id"]),
                "espera": {
                    "id": entrada["id"],
                    "motivo_label": entrada["motivo_label"],
                    "servicio_ideal": entrada["servicio_ideal"],
                    "servicio_ideal_label": entrada["servicio_ideal_label"],
                    "distrito": entrada["distrito"],
                    "franjas": entrada["franjas"],
                    "cupo": (
                        f"{opcion['servicio_nombre']} · {self._etiquetas.fecha_texto(opcion['fecha'])}, "
                        f"{opcion['hora_inicio']}–{opcion['hora_fin']}"
                        if opcion
                        else None
                    ),
                },
            },
        )

    # --- lectura ---

    def listar(self, desde: int = 0, limite: int = 200) -> dict:
        repo = self._estado.actividad
        return {"epoca": repo.epoca, "ultimo_id": repo.ultimo_id, "eventos": repo.desde(desde, limite)}

    # --- internos ---

    def _base(self, origen: str, estudiante_id: str | None) -> dict:
        return {
            "fecha_solicitud": self._estado.hoy.isoformat(),
            "origen": origen,
            "estudiante_id": estudiante_id,
        }

    def _cita(self, tipo: str, cita: Cita, comprobante: dict | None, origen: str, delta: int) -> dict:
        servicio = self._estado.motor.servicio(cita.service_id)
        info_servicio = {
            "service_id": cita.service_id,
            "nombre": cita.servicio_nombre,
            "tipo": cita.tipo,
            "tipo_label": cita.tipo_label,
            "distrito": servicio["distrito"] if servicio else cita.distrito,
        }
        ocupacion, antes_en_lote = self._ocupacion(cita.service_id, delta)
        evento = self._estado.actividad.agregar(
            tipo,
            {
                **self._base(origen, cita.estudiante_id),
                "servicio": info_servicio,
                "ocupacion": ocupacion,
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
            },
        )
        # El servicio cruzó el umbral de modo lote: el panel lo avisa aparte, una sola vez.
        if ocupacion and ocupacion["en_lote"] != antes_en_lote:
            self._estado.actividad.agregar(
                "servicio_en_lote" if ocupacion["en_lote"] else "servicio_sale_de_lote",
                {
                    **self._base(origen, None),
                    "servicio": info_servicio,
                    "ocupacion": ocupacion,
                    "umbral_pct": round(100 * umbral_lote(self._estado), 1),
                },
            )
        return evento

    def _ocupacion(self, service_id: str, delta: int) -> tuple[dict | None, bool]:
        """Ocupación del servicio ya con el evento aplicado (`delta` = lo que cambió: -1 al reservar) y
        si antes del evento estaba en modo lote."""
        _, _, por_servicio = embudo_por_servicio(self._estado)
        fila = por_servicio.get(service_id)
        if not fila:
            return None, False
        ahora = porcentaje(fila["reservados"], fila["liberados"])
        antes = porcentaje(fila["reservados"] + delta, fila["liberados"])
        return (
            {
                "pct": ahora,
                "antes_pct": antes,
                "reservados": fila["reservados"],
                "liberados": fila["liberados"],
                "nivel": nivel(self._estado, ahora),
                "en_lote": en_lote(self._estado, fila["reservados"], fila["liberados"]),
            },
            en_lote(self._estado, fila["reservados"] + delta, fila["liberados"]),
        )

    # --- lotes ---

    def lote_evento(self, tipo: str, lote_datos: dict, estudiante_id: str | None = None, origen: str = "chat") -> dict:
        """`lote_abierto`, `lote_solicitud` y `lote_resuelto`: `lote_datos` es el resumen que ve Coordinación."""
        return self._estado.actividad.agregar(
            tipo, {**self._base(origen, estudiante_id), "lote": lote_datos}
        )
