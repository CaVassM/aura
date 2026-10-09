"""Avisos para cada estudiante (p. ej. «tu lote se resolvió»), en RAM. Se vacían al reiniciar."""

from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

MAXIMO = 500


class AvisosRepository:
    def __init__(self) -> None:
        self.epoca = uuid4().hex[:8]
        self._eventos: list[dict] = []
        self._siguiente = 1
        self._lock = Lock()

    def agregar(self, estudiante_id: str, tipo: str, datos: dict) -> dict:
        with self._lock:
            evento = {
                "id": self._siguiente,
                "estudiante_id": estudiante_id,
                "tipo": tipo,
                "registrado_en": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                **datos,
            }
            self._siguiente += 1
            self._eventos.append(evento)
            del self._eventos[:-MAXIMO]
            return evento

    @property
    def ultimo_id(self) -> int:
        with self._lock:
            return self._siguiente - 1

    def desde(self, estudiante_id: str, ultimo_id: int, limite: int = MAXIMO) -> list[dict]:
        with self._lock:
            return [e for e in self._eventos if e["id"] > ultimo_id and e["estudiante_id"] == estudiante_id][:limite]


class AvisosDe:
    """Vista de los avisos de un estudiante con la misma forma que el registro de actividad (para el flujo SSE)."""

    def __init__(self, repo: AvisosRepository, estudiante_id: str) -> None:
        self._repo = repo
        self._estudiante_id = estudiante_id

    @property
    def epoca(self) -> str:
        return self._repo.epoca

    @property
    def ultimo_id(self) -> int:
        return self._repo.ultimo_id

    def desde(self, ultimo_id: int, limite: int = MAXIMO) -> list[dict]:
        return self._repo.desde(self._estudiante_id, ultimo_id, limite)
