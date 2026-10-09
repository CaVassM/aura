"""Lista de espera: si la persona no encontró cupo y lo acepta, se le avisa cuando se libere uno que le sirva.

El aviso llega por el flujo en vivo del estudiante (`/avisos/stream`) y como nota en su conversación, con la opción
lista para tocarla. No retiene el cupo: avisa y la persona decide; otra persona podría tomarlo antes.
Se revisa cada vez que se cancela una cita (lo único que libera cupos).
"""

import json

from aura.herramientas import validacion

from ..repositories.app_state import AppState
from .actividad_service import ActividadService
from .errors import InvalidRequestError, NotFoundError
from .etiquetas import Etiquetas


class ListaEsperaService:
    def __init__(self, estado: AppState):
        self._e = estado
        self._et = Etiquetas(estado.tablas)
        self._actividad = ActividadService(estado)

    # --- alta y baja ---

    def anotar(self, estudiante_id: str, solicitud: dict, sesion_id: str | None = None, origen: str = "chat") -> dict:
        """Anota a la persona con la solicitud que no tuvo cupo. Repetir la misma no la duplica."""
        with self._e.lock:
            probada = self._e.motor.proponer_opciones({**solicitud, "estudiante_id": estudiante_id}, 1)
            if probada.get("motivo_vacio") == "solicitud_invalida":
                raise InvalidRequestError(probada.get("detalle", "solicitud no válida"))
            firma = json.dumps(
                {k: solicitud.get(k) for k in ("motivo", "distrito", "franjas", "canales_aceptables", "fecha")},
                sort_keys=True,
                default=str,
            )
            existente = self._e.lista_espera.igual(estudiante_id, firma)
            if existente is not None:
                return existente
            motivo = str(solicitud["motivo"])
            ideal = self._e.tablas["motivo_a_servicio"].get(motivo, "")
            franjas = "; ".join(
                f"{self._et.dia_largo(validacion.indice_dia(f['dia']))} {f['desde']}–{f['hasta']}"
                for f in solicitud["franjas"]
            )
            entrada = self._e.lista_espera.agregar(
                estudiante_id,
                {**solicitud, "estudiante_id": estudiante_id},
                sesion_id,
                firma,
                {
                    "motivo": motivo,
                    "motivo_label": self._et.motivo(motivo),
                    "servicio_ideal": ideal,
                    "servicio_ideal_label": self._et.tipo(ideal),
                    "distrito": validacion.distrito(solicitud["distrito"], None),
                    "franjas": franjas,
                    "canales": list(validacion.canales(solicitud["canales_aceptables"])),
                },
            )
            self._actividad.lista_espera("lista_espera_alta", entrada, origen)
            return entrada

    def listar(self, estudiante_id: str) -> list[dict]:
        return self._e.lista_espera.de(estudiante_id)

    def cancelar(self, estudiante_id: str, espera_id: str) -> dict:
        with self._e.lock:
            entrada = self._e.lista_espera.obtener(espera_id)
            if entrada is None or entrada["estudiante_id"] != estudiante_id:
                raise NotFoundError(espera_id)
            if entrada["estado"] == "esperando":
                self._e.lista_espera.marcar(entrada, "cancelada")
            return entrada

    # --- aviso cuando se libera un cupo ---

    def revisar(self) -> list[dict]:
        """Busca para cada persona que espera (en orden de llegada) un cupo libre que le sirva y le avisa.

        Un mismo cupo se ofrece a una sola persona por revisión. Devuelve las entradas avisadas."""
        with self._e.lock:
            pendientes = self._e.lista_espera.esperando()
            if not pendientes:
                return []
            from .lote_service import LoteService  # import tardío: LoteService usa CitasService, que usa este servicio

            en_lote = LoteService(self._e).servicios_en_lote()
            ofrecidos: set[str] = set()
            avisadas = []
            for entrada in pendientes:
                propuesta = self._e.motor.proponer_opciones(entrada["solicitud"], 5, excluir_servicios=en_lote)
                opcion = next((o for o in propuesta["opciones"] if o["opcion_id"].split("|")[0] not in ofrecidos), None)
                if opcion is None:
                    continue
                ofrecidos.add(opcion["opcion_id"].split("|")[0])
                opcion["tipo_label"] = self._et.tipo(opcion["tipo"])
                self._e.lista_espera.marcar(entrada, "avisada", avisada_en=_ahora_iso(), opcion=opcion)
                self._avisar(entrada, opcion, propuesta.get("servicio_ideal"))
                self._actividad.lista_espera("lista_espera_aviso", entrada, "sistema")
                avisadas.append(entrada)
            return avisadas

    def _avisar(self, entrada: dict, opcion: dict, servicio_ideal: str | None) -> None:
        texto = (
            f"Se liberó un cupo que te sirve: {opcion['servicio_nombre']} ({opcion['tipo_label']}) · "
            f"{self._et.fecha_texto(opcion['fecha'])}, de {opcion['hora_inicio']} a {opcion['hora_fin']} · "
            f"{self._et.canal(opcion['canal'])}. Si lo quieres, tócalo y lo reservo; otra persona podría tomarlo antes."
        )
        self._e.avisos.agregar(
            entrada["estudiante_id"], "cupo_disponible", {"mensaje": texto, "espera_id": entrada["id"], "opciones": [opcion]}
        )
        sesion = self._e.chats.obtener(entrada["sesion_id"]) if entrada["sesion_id"] else None
        if sesion is None:
            return
        candado = self._e.chats.candado(sesion.id)
        if candado.acquire(timeout=1):  # si el agente está respondiendo ahora, no se le pisa el historial
            try:
                from langchain_core.messages import AIMessage

                # La opción queda como la «opción 1» de la conversación: tocarla o decir «la quiero» la reserva.
                sesion.propuestas = {opcion["opcion_id"]: opcion}
                sesion.ultima_solicitud = entrada["solicitud"]
                sesion.servicio_ideal = servicio_ideal
                sesion.desencuentro_registrado = False
                sesion.mensajes.append(AIMessage(texto))
            except ImportError:  # sin LangChain no hay chat que actualizar
                pass
            finally:
                candado.release()


def _ahora_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")
