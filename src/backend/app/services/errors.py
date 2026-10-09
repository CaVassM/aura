"""Errores de dominio de la plataforma; main.py los traduce a respuestas HTTP."""


class PlatformError(Exception):
    """Base de los errores esperados de la plataforma."""

    status_code = 400
    code = "error"

    def __init__(self, detalle: str = ""):
        super().__init__(detalle or self.code)
        self.detalle = detalle


class NotFoundError(PlatformError):
    status_code = 404
    code = "no_encontrado"


class SlotTakenError(PlatformError):
    status_code = 409
    code = "cupo_ya_tomado"


class InvalidRequestError(PlatformError):
    status_code = 422
    code = "solicitud_invalida"


class AgenteNoDisponibleError(PlatformError):
    status_code = 503
    code = "agente_no_disponible"


class YaEnLoteError(PlatformError):
    status_code = 409
    code = "ya_en_lote"
