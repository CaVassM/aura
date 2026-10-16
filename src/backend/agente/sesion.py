"""Estado de una conversación. Es Python puro: lo guarda la plataforma, en RAM."""

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ContextoEstudiante:
    """Datos que el portal ya conoce de la persona; el agente no se los vuelve a pedir."""

    distrito: str | None = None
    grupo: str | None = None  # "diurno" | "nocturno"


@dataclass
class SesionChat:
    id: str
    estudiante_id: str
    contexto: ContextoEstudiante = field(default_factory=ContextoEstudiante)
    mensajes: list = field(default_factory=list)  # historial LangChain (Human/AI/Tool)
    propuestas: dict[str, dict] = field(default_factory=dict)  # opcion_id → opción de la última propuesta
    servicio_ideal: str | None = None
    ultima_solicitud: dict | None = None  # para registrar el desencuentro sin que el modelo la repita
    desencuentro_registrado: bool = False
    desencuentros_firmas: set = field(default_factory=set)  # (servicio ideal, franjas) ya registrados: un solo desencuentro por conversación
    reemplazo_pendiente: dict | None = None  # R7: `{opcion_id}` que choca con una cita activa; espera que la persona confirme
    lote_id: int | None = None  # lote en el que quedó esperando
    actualizada_en: str = ""

    def tocar(self) -> None:
        self.actualizada_en = datetime.now(timezone.utc).isoformat(timespec="seconds")
