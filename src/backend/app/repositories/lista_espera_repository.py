"""Lista de espera (RAM): personas que no encontraron cupo y quieren que se les avise si se libera uno.

Se vacía al reiniciar el proceso o la demo. El orden de llegada decide a quién se avisa primero.
"""

from datetime import datetime, timezone
from threading import RLock

ESTADOS = ("esperando", "avisada", "cancelada")


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ListaEsperaRepository:
    def __init__(self) -> None:
        self._entradas: dict[str, dict] = {}
        self._siguiente = 1
        self.lock = RLock()

    def agregar(self, estudiante_id: str, solicitud: dict, sesion_id: str | None, firma: str, resumen: dict) -> dict:
        with self.lock:
            entrada = {
                "id": f"ESP-{self._siguiente:04d}",
                "estudiante_id": estudiante_id,
                "solicitud": solicitud,
                "sesion_id": sesion_id,
                "firma": firma,
                "estado": "esperando",
                "creada_en": _ahora(),
                "avisada_en": None,
                "opcion": None,
                **resumen,
            }
            self._siguiente += 1
            self._entradas[entrada["id"]] = entrada
            return entrada

    def obtener(self, espera_id: str) -> dict | None:
        return self._entradas.get(espera_id)

    def esperando(self) -> list[dict]:
        """En orden de llegada."""
        with self.lock:
            return [e for e in self._entradas.values() if e["estado"] == "esperando"]

    def de(self, estudiante_id: str) -> list[dict]:
        """Las de la persona, la más reciente primero."""
        with self.lock:
            return [e for e in reversed(list(self._entradas.values())) if e["estudiante_id"] == estudiante_id]

    def igual(self, estudiante_id: str, firma: str) -> dict | None:
        with self.lock:
            return next(
                (e for e in self._entradas.values() if e["estudiante_id"] == estudiante_id and e["firma"] == firma and e["estado"] == "esperando"),
                None,
            )

    def marcar(self, entrada: dict, estado: str, **datos) -> None:
        with self.lock:
            entrada["estado"] = estado
            entrada.update(datos)
