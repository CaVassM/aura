"""Citas de estudiantes: propone, reserva y cancela sobre el estado compartido."""

from ..models import Cita
from ..repositories.app_state import AppState
from .actividad_service import ActividadService
from .etiquetas import Etiquetas
from .errors import InvalidRequestError, NotFoundError, SlotTakenError


class CitasService:
    """Lógica de citas; el motor decide disponibilidad y asignación."""

    def __init__(self, estado: AppState):
        self._estado = estado
        self._etiquetas = Etiquetas(estado.tablas)
        self._actividad = ActividadService(estado)

    def proponer(self, solicitud: dict, k: int = 3) -> dict:
        """Opciones compatibles sin reservar; una solicitud inválida es un 422."""
        resultado = self._estado.motor.proponer_opciones(solicitud, k)
        if resultado.get("motivo_vacio") == "solicitud_invalida":
            raise InvalidRequestError(resultado.get("detalle", ""))
        for opcion in resultado["opciones"]:
            opcion["tipo_label"] = self._etiquetas.tipo(opcion["tipo"])
        return resultado

    def reservar(
        self,
        estudiante_id: str,
        opcion_id: str,
        servicio_ideal: str | None = None,
        origen: str = "api",
    ) -> Cita:
        """Reserva en el motor y registra la cita; visible de inmediato en coordinación.

        `origen` (`api` o `chat`) solo sirve para el registro de actividad en vivo."""
        with self._estado.lock:
            resultado = self._estado.motor.reservar(estudiante_id, opcion_id, servicio_ideal)
            if resultado.get("error") == "cupo_fuera_de_ventana":
                raise InvalidRequestError("El cupo está fuera de la ventana de reserva (hoy + 1 a hoy + 14 días)")
            if resultado.get("error") == "opcion_invalida":
                raise InvalidRequestError(resultado.get("detalle", "opcion_id no válido"))
            if not resultado["ok"]:
                raise SlotTakenError(opcion_id)
            cita = self._estado.citas.add(Cita.desde_comprobante(resultado["cita"], self._etiquetas.tipo))
            self._actividad.cita_reservada(cita, resultado["cita"], origen)
            return cita

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
            return cita

    def registrar_desencuentro(self, solicitud: dict, origen: str = "api") -> dict:
        """Guarda en el motor una solicitud sin opciones y deja el aviso en la actividad en vivo."""
        with self._estado.lock:
            resultado = self._estado.motor.registrar_desencuentro(solicitud)
            if resultado.get("ok"):
                fila = next(d for d in reversed(self._estado.desencuentros) if d["registro_id"] == resultado["registro_id"])
                self._actividad.desencuentro(fila, origen)
            return resultado
