"""Detección simple de señales de crisis y respuesta fija.

No sustituye el criterio del modelo (el prompt también le indica qué hacer): es una red de
seguridad determinista para que ante estas frases la persona siempre vea los recursos de ayuda.
El texto y las líneas de ayuda son un SUPUESTO por validar con Bienestar (ver decisiones_pendientes.md).
"""

import re
import unicodedata

_SENALES = [
    r"suicid",
    r"quitarme la vida",
    r"quitarle la vida",
    r"matarme",
    r"acabar con mi vida",
    r"acabar con todo",
    r"terminar con mi vida",
    r"no quiero vivir",
    r"no quiero seguir viviendo",
    r"no vale la pena vivir",
    r"mejor estar muert",
    r"quiero morir",
    r"quisiera morir",
    r"hacerme dano",
    r"lastimarme",
    r"autolesion",
]
_PATRON = re.compile("|".join(_SENALES))

MENSAJE_CRISIS = (
    "Lamento mucho que estés pasando por esto, y me alegra que me lo cuentes. Tu seguridad es lo más "
    "importante ahora. Si sientes que puedes hacerte daño o estás en peligro, busca ayuda inmediata: "
    "llama a la Línea 113, opción 5 (salud mental, MINSA, gratuita), o acude a la emergencia del hospital "
    "más cercano. Si hay alguien de confianza cerca, avísale y no te quedes a solas. "
    "Yo no puedo brindarte atención de crisis, pero sí puedo ayudarte a agendar con el servicio de "
    "bienestar cuando quieras. ¿Quieres que lo hagamos?"
)


def _sin_tildes(texto: str) -> str:
    base = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


def detectar_crisis(texto: str) -> bool:
    return bool(_PATRON.search(_sin_tildes(texto)))
