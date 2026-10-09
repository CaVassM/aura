"""Errores del agente que la plataforma traduce a respuestas HTTP."""


class AgenteNoDisponible(Exception):
    """El modelo no responde (Ollama apagado, modelo sin descargar, dependencias sin instalar)."""
