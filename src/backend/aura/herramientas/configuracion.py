"""Lectura de configuración de AURA y resolución de la ruta externa de datos."""

import os
from pathlib import Path
import yaml

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]


def cargar_yaml(nombre: str) -> dict:
    """Carga un YAML UTF-8 ubicado en config/ junto al paquete de la aplicación."""
    ruta = RAIZ_PROYECTO / "config" / nombre
    with ruta.open(encoding="utf-8") as archivo:
        return yaml.safe_load(archivo)


def ruta_data_pack() -> Path:
    """Ruta del Data Pack: variable AURA_DATA_DIR o, si no existe, `data_pack_path` del YAML."""
    externa = os.environ.get("AURA_DATA_DIR")
    if externa:
        return Path(externa).expanduser().resolve()
    return (RAIZ_PROYECTO / cargar_yaml("parametros.yaml")["data_pack_path"]).resolve()


def ruta_d5() -> Path:
    """Ruta del JSON de D5: variable AURA_D5_PATH o, si no existe, `d5_path` del YAML."""
    externa = os.environ.get("AURA_D5_PATH")
    if externa:
        return Path(externa).expanduser().resolve()
    return (RAIZ_PROYECTO / cargar_yaml("parametros.yaml")["d5_path"]).resolve()
