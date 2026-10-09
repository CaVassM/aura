"""Configuración del agente, tomada del entorno (y de un `.env` si existe python-dotenv)."""

import os
from dataclasses import dataclass

try:  # opcional: solo para comodidad en local
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass


def _entero(nombre: str, defecto: int) -> int:
    try:
        return int(os.environ.get(nombre, defecto))
    except ValueError:
        return defecto


def _decimal(nombre: str, defecto: float) -> float:
    try:
        return float(os.environ.get(nombre, defecto))
    except ValueError:
        return defecto


def _razonamiento(nombre: str) -> bool | str | None:
    """`false` apaga el «pensar» del modelo, `true` lo enciende, `low|medium|high` fija el nivel; vacío = el del modelo."""
    valor = os.environ.get(nombre, "").strip().lower()
    if valor in {"false", "0", "no", "off"}:
        return False
    if valor in {"true", "1", "si", "sí", "on"}:
        return True
    return valor if valor in {"low", "medium", "high"} else None


@dataclass(frozen=True)
class ConfigAgente:
    """Variables: AURA_OLLAMA_MODEL, AURA_OLLAMA_URL, AURA_OLLAMA_TEMPERATURE, AURA_OLLAMA_NUM_CTX,
    AURA_OLLAMA_TIMEOUT, AURA_OLLAMA_REASONING, AURA_OLLAMA_KEEP_ALIVE, AURA_LINEA_AYUDA, AURA_AGENTE_MAX_PASOS,
    AURA_AGENTE_MAX_TURNOS."""

    modelo: str = "gemma4"
    url: str = "http://localhost:11434"
    temperatura: float = 0.2
    num_ctx: int = 8192  # el contexto por defecto de Ollama no alcanza para prompt + herramientas
    timeout_s: int = 120
    razonamiento: bool | str | None = None  # None: el modelo decide; False: sin «pensar» (más rápido)
    linea_ayuda: str = ""  # texto de la línea de ayuda propia de la red, para el mensaje de crisis
    keep_alive: str = "30m"  # cuánto queda el modelo cargado en memoria tras el último mensaje
    max_pasos: int = 10  # llamadas al modelo/herramientas por mensaje antes de rendirse
    max_turnos: int = 12  # mensajes de la persona que se conservan en el historial

    @classmethod
    def desde_entorno(cls) -> "ConfigAgente":
        return cls(
            modelo=os.environ.get("AURA_OLLAMA_MODEL", cls.modelo),
            url=os.environ.get("AURA_OLLAMA_URL", cls.url).rstrip("/"),
            temperatura=_decimal("AURA_OLLAMA_TEMPERATURE", cls.temperatura),
            num_ctx=_entero("AURA_OLLAMA_NUM_CTX", cls.num_ctx),
            timeout_s=_entero("AURA_OLLAMA_TIMEOUT", cls.timeout_s),
            razonamiento=_razonamiento("AURA_OLLAMA_REASONING"),
            keep_alive=os.environ.get("AURA_OLLAMA_KEEP_ALIVE", cls.keep_alive),
            linea_ayuda=os.environ.get("AURA_LINEA_AYUDA", cls.linea_ayuda),
            max_pasos=_entero("AURA_AGENTE_MAX_PASOS", cls.max_pasos),
            max_turnos=_entero("AURA_AGENTE_MAX_TURNOS", cls.max_turnos),
        )
