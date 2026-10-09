"""Registro en RAM de lo que ocurre en vivo (citas reservadas o canceladas, desencuentros).

Solo guarda lo **nuevo**: lo que llegue por la API o por el chat después de arrancar. Las citas
sembradas de la demo no pasan por aquí. Se vacía al reiniciar el proceso o la demo.
"""

from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

MAXIMO = 1000  # tope para no crecer sin límite en una demo larga


class ActividadRepository:
    def __init__(self) -> None:
        # Cambia en cada reinicio de la demo: los clientes conectados lo notan y vacían su lista.
        self.epoca = uuid4().hex[:8]
        self._eventos: list[dict] = []
        self._siguiente = 1
        self._lock = Lock()

    def agregar(self, tipo: str, datos: dict) -> dict:
        with self._lock:
            evento = {
                "id": self._siguiente,
                "tipo": tipo,
                "registrado_en": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                **datos,
            }
            self._siguiente += 1
            self._eventos.append(evento)
            del self._eventos[:-MAXIMO]
            return evento

    def desde(self, ultimo_id: int, limite: int = MAXIMO) -> list[dict]:
        """Eventos con id mayor que `ultimo_id`, del más antiguo al más reciente."""
        with self._lock:
            return [e for e in self._eventos if e["id"] > ultimo_id][:limite]

    @property
    def ultimo_id(self) -> int:
        with self._lock:
            return self._siguiente - 1
