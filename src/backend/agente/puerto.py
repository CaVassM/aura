"""Lo que el agente necesita de la plataforma. La plataforma lo implementa (app/services/chat_service.py).

Todos los métodos devuelven diccionarios JSON y **no lanzan** por errores esperados: devuelven
`{"ok": False, "error": <código>, "detalle": <texto>}` para que el modelo pueda explicárselo a la persona.
"""

from typing import Protocol


class PuertoAgenda(Protocol):
    def proponer(self, solicitud: dict, k: int) -> dict:
        """`{"opciones": [...], "servicio_ideal": ...}` o `{"opciones": [], "motivo_vacio": ..., "detalle": ...}`."""

    def reservar(
        self,
        estudiante_id: str,
        opcion_id: str,
        servicio_ideal: str | None,
        solicitud: dict | None = None,
        sesion_id: str | None = None,
        reemplazar: bool = False,
    ) -> dict:
        """Una opción de `proponer`. Cupo: `{"ok": True, "estado": "confirmada", "cita": {...}}`. Servicio en lote
        (`LOTE|<servicio>`, necesita `solicitud`): `{"ok": True, "estado": "pendiente", "lote": {...}, "mensaje": ...}`.
        R7: si ya tiene una cita activa de ese tipo, `{"ok": False, "error": "ya_tiene_cita", "cita": {...}, "mensaje": ...}`;
        con `reemplazar` se cancela esa cita al reservar la nueva. Otros errores: `{"ok": False, "error": ...}`."""

    def cancelar(self, cita_id: str, estudiante_id: str) -> dict:
        """`{"ok": True, "cita": {...}}` o `{"ok": False, "error": ...}`."""

    def listar_citas(self, estudiante_id: str) -> list[dict]:
        """Citas de la persona (confirmadas y canceladas), la más reciente primero."""

    def anotar_lista_espera(self, solicitud: dict, estudiante_id: str, sesion_id: str) -> dict:
        """`{"ok": True, "espera": {id, ...}}` o `{"ok": False, ...}`: avisar a la persona si se libera un cupo que le sirva."""

    def asistencia(self, estudiante_id: str) -> dict:
        """Lo único académico que ve el agente: `{"ok": True, "asistencia_actual": ..., "cursos": [...]}` o `{"ok": False, ...}`.
        Solo asistencia: sin notas, créditos ni alertas."""

    def registrar_desencuentro(self, solicitud: dict) -> dict:
        """`{"ok": True, "registro_id": ...}` o `{"ok": False, "error": ...}`. Solo registra si no existe ningún cupo
        compatible (ni normal ni en lote); si existe alguno, `hay_cupos_compatibles`."""
