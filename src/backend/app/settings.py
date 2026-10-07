"""Configuración de la API tomada del entorno."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from aura.herramientas.configuracion import ruta_data_pack

ORIGENES_BASE = ("http://localhost:3000", "http://localhost:5173")


@dataclass(frozen=True)
class Settings:
    """AURA_DATA_DIR: Data Pack (si falta, `data_pack_path` de parametros.yaml).
    AURA_CORS_ORIGINS: orígenes extra separados por coma."""

    data_dir: Path
    cors_origins: tuple[str, ...] = field(default=ORIGENES_BASE)

    @classmethod
    def desde_entorno(cls) -> "Settings":
        extra = [
            o.strip()
            for o in os.environ.get("AURA_CORS_ORIGINS", "").split(",")
            if o.strip()
        ]
        return cls(data_dir=ruta_data_pack(), cors_origins=ORIGENES_BASE + tuple(extra))
