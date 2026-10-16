"""Citas de estudiantes: propone, reserva y cancela sobre el estado compartido."""

from ..models import Cita
from ..repositories.app_state import AppState
from .actividad_service import ActividadService
from .etiquetas import Etiquetas
from .lista_espera_service import ListaEsperaService
from .lote_service import LoteService
from .errors import InvalidRequestError, NotFoundError, SlotTakenError, YaTieneCitaError


TOPE_CITAS_ACTIVAS = 2


class CitasService:
    """Lógica de citas; el motor decide disponibilidad y asignación."""

    def __init__(self, estado: AppState):
        self._estado = estado
        self._etiquetas = Etiquetas(estado.tablas)
        self._actividad = ActividadService(estado)

    def proponer(self, solicitud: dict, k: int = 3) -> dict:
        """Hasta `max_opciones` (3) opciones compatibles sin reservar; una solicitud inválida es un 422.

        El servicio ideal (o el que la persona nombró en `service_id_preferido`) va primero y las alternativas afines solo
        completan. Un servicio en modo lote (utilización ≥ umbral) no se oculta: sale como UNA opción de tipo `lote`
        (`opcion_id` = `LOTE|<servicio>`), ordenada con el costo de su mejor cupo. Trae `mensaje` para los casos
        especiales (sin cupos, servicio en lote, servicio pedido sin cupo)."""
        lotes = LoteService(self._estado)
        resultado = self._estado.motor.proponer_opciones(
            solicitud, k, servicios_lote=lotes.servicios_en_lote(), ventana_lote_s=lotes.ventana_s
        )
        if resultado.get("motivo_vacio") == "solicitud_invalida":
            raise InvalidRequestError(resultado.get("detalle", ""))
        otra = (resultado.get("preferido") or {}).get("mejor_alternativa_mismo_tipo")
        for opcion in resultado["opciones"] + ([otra] if otra else []):
            opcion["tipo_label"] = self._etiquetas.tipo(opcion["tipo"])
        return resultado

    # --- R7: equidad ---

    def cita_activa_de_tipo(self, estudiante_id: str, tipo: str) -> Cita | None:
        """La cita activa (confirmada y por venir) que ya ocupa el cupo permitido de ese tipo de servicio, si lo ocupa.

        R7: máximo `max_citas_activas_por_tipo` (1) por persona y tipo de servicio dentro del horizonte."""
        maximo = int(self._estado.parametros.get("max_citas_activas_por_tipo", 1))
        hoy = self._estado.hoy.isoformat()
        activas = sorted(
            (c for c in self.listar(estudiante_id) if c.estado == "confirmada" and c.tipo == tipo and c.fecha >= hoy),
            key=lambda c: (c.fecha, c.hora_inicio),
        )
        return activas[0] if len(activas) >= maximo else None

    def datos_cita(self, cita: Cita) -> dict:
        """La cita tal como la ve quien consulta el conflicto: servicio, día, hora y canal."""
        return {
            "id": cita.id,
            "servicio_nombre": cita.servicio_nombre,
            "tipo": cita.tipo,
            "tipo_label": cita.tipo_label,
            "distrito": cita.distrito,
            "fecha": cita.fecha,
            "dia_semana": self._etiquetas.fecha_texto(cita.fecha).split(" ")[0],
            "hora_inicio": cita.hora_inicio,
            "hora_fin": cita.hora_fin,
            "canal": cita.canal,
            "canal_label": self._etiquetas.canal(cita.canal),
        }

    def mensaje_ya_tiene(self, cita: Cita) -> str:
        dia, numero = self._etiquetas.fecha_texto(cita.fecha).split(" ")[:2]
        return (
            f"Ya tienes una cita de {cita.tipo_label.lower()} el {dia} {numero} a las {cita.hora_inicio}. "
            "¿Quieres cambiarla por esta?"
        )

    def verificar_equidad(self, estudiante_id: str, tipo: str | None, reemplazar: bool = False) -> Cita | None:
        """R7. Sin conflicto devuelve None; con conflicto y `reemplazar`, la cita que se cancelará al reservar la nueva;
        con conflicto y sin `reemplazar`, `ya_tiene_cita`."""
        previa = self.cita_activa_de_tipo(estudiante_id, tipo) if tipo else None
        if previa and not reemplazar:
            raise YaTieneCitaError(self.datos_cita(previa), self.mensaje_ya_tiene(previa))
        return previa

    # --- reservar ---

    def reservar(
        self,
        estudiante_id: str,
        opcion_id: str,
        servicio_ideal: str | None = None,
        origen: str = "api",
        reemplazar: bool = False,
    ) -> Cita:
        """Reserva en el motor y registra la cita; visible de inmediato en coordinación.

        R7: si ya tiene una cita activa de ese tipo de servicio, falla con `ya_tiene_cita`; con `reemplazar` se reserva la
        nueva y se cancela la anterior en la misma operación. `origen` solo sirve para el registro de actividad."""
        with self._estado.lock:
            activas = [c for c in self._estado.citas.list_by_student(estudiante_id) if c.estado == "confirmada"]
            if len(activas) >= TOPE_CITAS_ACTIVAS:
                raise InvalidRequestError(
                    f"Has alcanzado el l\u00edmite de {TOPE_CITAS_ACTIVAS} citas activas. Cancela una antes de agendar otra."
                )
            previa = self.verificar_equidad(estudiante_id, self._estado.motor.tipo_de_opcion(opcion_id), reemplazar)
            resultado = self._estado.motor.reservar(estudiante_id, opcion_id, servicio_ideal)
            if resultado.get("error") == "cupo_fuera_de_ventana":
                raise InvalidRequestError("El cupo está fuera de la ventana de reserva (hoy + 1 a hoy + 14 días)")
            if resultado.get("error") == "opcion_invalida":
                raise InvalidRequestError(resultado.get("detalle", "opcion_id no válido"))
            if not resultado["ok"]:
                raise SlotTakenError(opcion_id)
            cita = self._estado.citas.add(Cita.desde_comprobante(resultado["cita"], self._etiquetas.tipo))
            self._actividad.cita_reservada(cita, resultado["cita"], origen)
            if previa:  # «cambiarla»: la anterior se libera solo ahora que la nueva quedó reservada
                self.cancelar(previa.id, estudiante_id, origen)
            return cita

    def reservar_opcion(
        self,
        estudiante_id: str,
        opcion_id: str,
        servicio_ideal: str | None = None,
        origen: str = "chat",
        solicitud: dict | None = None,
        sesion_id: str | None = None,
        reemplazar: bool = False,
    ) -> dict:
        """Reserva cualquier opción de `proponer`: un cupo (`estado: confirmada`, con la cita) o un servicio en lote
        (`estado: pendiente`: la solicitud queda inscrita en el lote y el resultado llega después al chat)."""
        clave, _, service_id = opcion_id.partition("|")
        if clave != "LOTE":
            return {"estado": "confirmada", "cita": self.reservar(estudiante_id, opcion_id, servicio_ideal, origen, reemplazar)}
        if not solicitud:
            raise InvalidRequestError("Para entrar a un lote hace falta la solicitud con las preferencias de la persona")
        entrada = LoteService(self._estado).entrar(
            estudiante_id, solicitud, sesion_id, origen, service_id=service_id, reemplazar=reemplazar
        )
        servicio = self._estado.motor.servicio(service_id)
        nombre = servicio["nombre"] if servicio else service_id
        return {
            "estado": "pendiente",
            "lote": entrada["lote"],
            "servicio_nombre": nombre,
            "mensaje": (
                f"Quedaste en el lote de {nombre}. Se asigna en conjunto y se cierra solo en unos segundos (o antes si se "
                "llena): te aviso aquí con tu cita."
            ),
        }

    def listar(self, estudiante_id: str) -> list[Cita]:
        return self._estado.citas.list_by_student(estudiante_id)

    def cancelar(self, cita_id: str, estudiante_id: str | None = None, origen: str = "api") -> Cita:
        """Cancela y libera el cupo; si se indica estudiante, debe ser el dueño."""
        with self._estado.lock:
            cita = self._estado.citas.get(cita_id)
            if cita is None or (estudiante_id and cita.estudiante_id != estudiante_id):
                raise NotFoundError(cita_id)
            if cita.estado == "confirmada":
                self._estado.motor.cancelar_cita(cita_id)
                cita.estado = "cancelada"
                self._actividad.cita_cancelada(cita, origen)
                ListaEsperaService(self._estado).revisar()  # el cupo liberado puede servirle a alguien que espera
            return cita

    def registrar_desencuentro(self, solicitud: dict, origen: str = "api", verificar: bool = False) -> dict:
        """Guarda en el motor una solicitud sin opciones y deja el aviso en la actividad en vivo.

        Un desencuentro es que NO exista ningún cupo compatible, ni normal ni en lote, dentro de la ventana y las
        restricciones de la persona. Con `verificar` se comprueba antes (sin la fecha concreta ni el servicio pedido, que
        solo son preferencias) y, si existe alguno, se rechaza con `hay_cupos_compatibles`."""
        with self._estado.lock:
            if verificar:
                amplia = {k: v for k, v in solicitud.items() if k not in ("fecha", "service_id_preferido")}
                lotes = LoteService(self._estado)
                hay = self._estado.motor.proponer_opciones(amplia, 1, servicios_lote=lotes.servicios_en_lote())
                if hay.get("opciones"):
                    return {
                        "ok": False,
                        "error": "hay_cupos_compatibles",
                        "detalle": "Hay cupos compatibles (también por lote): eso no es un desencuentro. Muéstrale las opciones.",
                    }
            resultado = self._estado.motor.registrar_desencuentro(solicitud)
            if resultado.get("ok"):
                fila = next(d for d in reversed(self._estado.desencuentros) if d["registro_id"] == resultado["registro_id"])
                self._actividad.desencuentro(fila, origen)
            return resultado
