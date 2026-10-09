"""Lo que el agente necesita de la plataforma. La plataforma lo implementa (app/services/chat_service.py).

Todos los métodos devuelven diccionarios JSON y **no lanzan** por errores esperados: devuelven
`{"ok": False, "error": <código>, "detalle": <texto>}` para que el modelo pueda explicárselo a la persona.
"""

from typing import Protocol


class PuertoAgenda(Protocol):
    def proponer(self, solicitud: dict, k: int) -> dict:
        """`{"opciones": [...], "servicio_ideal": ...}` o `{"opciones": [], "motivo_vacio": ..., "detalle": ...}`."""

    def reservar(self, estudiante_id: str, opcion_id: str, servicio_ideal: str | None) -> dict:
        """`{"ok": True, "cita": {...}}` o `{"ok": False, "error": ...}`."""

    def cancelar(self, cita_id: str, estudiante_id: str) -> dict:
        """`{"ok": True, "cita": {...}}` o `{"ok": False, "error": ...}`."""

    def listar_citas(self, estudiante_id: str) -> list[dict]:
        """Citas de la persona (confirmadas y canceladas), la más reciente primero."""

    def entrar_a_lote(self, solicitud: dict, estudiante_id: str, sesion_id: str) -> dict:
        """`{"ok": True, "lote": {id, estado, posicion, solicitudes, tamano_maximo, cierra_en}}` o `{"ok": False, ...}`."""

    def registrar_desencuentro(self, solicitud: dict) -> dict:
        """`{"ok": True, "registro_id": ...}` o `{"ok": False, "error": ...}`."""
