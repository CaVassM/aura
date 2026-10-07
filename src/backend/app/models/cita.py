"""Cita de un estudiante, tal como la ve la plataforma."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Cita:
    """Cita confirmada o cancelada; el cupo real lo gestiona el motor de asignación."""

    id: str
    estudiante_id: str
    cupo_id: str
    opcion_id: str
    service_id: str
    servicio_nombre: str
    tipo: str
    tipo_label: str
    distrito: str
    fecha: str
    hora_inicio: str
    hora_fin: str
    canal: str
    estado: str = "confirmada"
    creada_en: str = ""

    def __post_init__(self) -> None:
        if not self.creada_en:
            self.creada_en = datetime.now(timezone.utc).isoformat(timespec="seconds")

    @classmethod
    def desde_comprobante(cls, comprobante: dict, etiqueta_tipo=lambda t: t) -> "Cita":
        """Construye la cita desde el comprobante del motor; `etiqueta_tipo` traduce el tipo."""
        return cls(
            id=comprobante["cita_id"],
            estudiante_id=comprobante["estudiante_id"],
            cupo_id=comprobante["cupo_id"],
            opcion_id=comprobante["opcion_id"],
            service_id=comprobante["service_id"],
            servicio_nombre=comprobante["servicio_nombre"],
            tipo=comprobante["tipo"],
            tipo_label=etiqueta_tipo(comprobante["tipo"]),
            distrito=comprobante["distrito"],
            fecha=comprobante["fecha"],
            hora_inicio=comprobante["hora_inicio"],
            hora_fin=comprobante["hora_fin"],
            canal=comprobante["canal"],
        )
