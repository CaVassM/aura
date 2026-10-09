"""Lotes en RAM: el lote abierto, su cuenta regresiva y el historial de los ya resueltos."""

from dataclasses import dataclass, field
from threading import RLock

MAX_HISTORIAL = 50


@dataclass
class SolicitudLote:
    estudiante_id: str
    solicitud: dict  # preferencias, como las de proponer_opciones
    sesion_id: str | None
    posicion: int  # orden de llegada dentro del lote (desde 1)
    entrada_en: str  # ISO UTC
    origen: str  # chat | api

    @property
    def clave(self) -> str:
        """Id de la solicitud dentro del plan del motor (`NNN|<estudiante>`)."""
        return f"{self.posicion:03d}|{self.estudiante_id}"


@dataclass
class Lote:
    id: int
    abierto_en: str
    cierra_en: str
    estado: str = "abierto"  # abierto -> resolviendo -> resuelto
    cerrado_en: str | None = None
    solicitudes: list[SolicitudLote] = field(default_factory=list)
    resultado: dict | None = None
    timer: object | None = None  # threading.Timer que lo cierra solo


class LoteRepository:
    def __init__(self) -> None:
        self.lock = RLock()
        self.abierto: Lote | None = None
        self.historial: list[Lote] = []  # el más reciente primero
        self._siguiente = 1

    def nuevo_id(self) -> int:
        with self.lock:
            numero = self._siguiente
            self._siguiente += 1
            return numero

    def archivar(self, lote: Lote) -> None:
        with self.lock:
            self.historial.insert(0, lote)
            del self.historial[MAX_HISTORIAL:]
