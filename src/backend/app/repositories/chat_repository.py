"""Sesiones de chat en RAM; se vacían al reiniciar el proceso o la demo."""

from threading import Lock, RLock
from uuid import uuid4

from agente.sesion import ContextoEstudiante, SesionChat

MAX_SESIONES = 500  # tope para no crecer sin límite en una demo larga


class ChatRepository:
    def __init__(self) -> None:
        self._sesiones: dict[str, SesionChat] = {}
        self._candados: dict[str, RLock] = {}
        self._lock = Lock()

    def obtener(self, session_id: str) -> SesionChat | None:
        return self._sesiones.get(session_id)

    def crear(self, estudiante_id: str, contexto: ContextoEstudiante) -> SesionChat:
        with self._lock:
            if len(self._sesiones) >= MAX_SESIONES:  # descarta la menos reciente
                vieja = min(self._sesiones.values(), key=lambda s: s.actualizada_en)
                self._sesiones.pop(vieja.id, None)
                self._candados.pop(vieja.id, None)
            sesion = SesionChat(uuid4().hex, estudiante_id, contexto)
            sesion.tocar()
            self._sesiones[sesion.id] = sesion
            self._candados[sesion.id] = RLock()
            return sesion

    def candado(self, session_id: str) -> RLock:
        """Un mensaje a la vez por sesión: el historial no admite dos turnos en paralelo."""
        with self._lock:
            return self._candados.setdefault(session_id, RLock())

    def eliminar(self, session_id: str) -> bool:
        with self._lock:
            self._candados.pop(session_id, None)
            return self._sesiones.pop(session_id, None) is not None
