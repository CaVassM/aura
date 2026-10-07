"""Almacén en RAM de citas; se vacía al reiniciar el proceso."""

from threading import Lock

from ..models import Cita


class CitaRepository:
    """Guarda y consulta citas por identificador y por estudiante."""

    def __init__(self) -> None:
        self._citas: dict[str, Cita] = {}
        self._lock = Lock()

    def add(self, cita: Cita) -> Cita:
        with self._lock:
            self._citas[cita.id] = cita
        return cita

    def get(self, cita_id: str) -> Cita | None:
        return self._citas.get(cita_id)

    def list_by_student(self, estudiante_id: str) -> list[Cita]:
        """Citas del estudiante, la más reciente primero."""
        citas = [c for c in list(self._citas.values()) if c.estudiante_id == estudiante_id]
        return sorted(citas, key=lambda c: c.creada_en, reverse=True)

    def list_all(self) -> list[Cita]:
        return list(self._citas.values())
