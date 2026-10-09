"""Detección simple de señales de crisis y respuesta fija.

No sustituye el criterio del modelo (el prompt también le indica qué hacer): es una red de
seguridad determinista para que ante estas frases la persona siempre vea los recursos de ayuda.
La red (Aethera) es ficticia: el texto no nombra líneas reales; la línea propia se configura con AURA_LINEA_AYUDA
(ver decisiones_pendientes.md).
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
    r"hacer(me)? (dano|mal)",
    r"lastimarme",
    r"autolesion",
    r"terminar con todo",
    r"no quiero estar viv[oa]",
    r"(quiero|quisiera|queria|ojala pudiera) desaparecer",
    r"desaparecer (del mundo|para siempre)",
    r"sentido a (la vida|nada)",
    r"sentido (de|para) (seguir|vivir)",
]
_PATRON = re.compile(re.sub(r"([a-z])\1+", r"\1", "|".join(_SENALES)))

LINEA_POR_DEFECTO = "la línea de ayuda de tu institución"


def mensaje_crisis(linea_ayuda: str = "") -> str:
    """Texto fijo de ayuda inmediata. `linea_ayuda` (p. ej. «la Línea de Bienestar 0800-123») sale de AURA_LINEA_AYUDA."""
    linea = linea_ayuda.strip() or LINEA_POR_DEFECTO
    return (
        "Lamento mucho que estés pasando por esto, y me alegra que me lo cuentes. Tu seguridad es lo más "
        "importante ahora. Si sientes que puedes hacerte daño o estás en peligro, busca ayuda inmediata: "
        f"comunícate ahora con los servicios de emergencia de tu zona o con {linea}, o acude al centro de "
        "salud más cercano. Si hay alguien de confianza cerca, avísale y no te quedes a solas. "
        "Yo no puedo brindarte atención de crisis, pero sí puedo ayudarte a agendar con el servicio de "
        "bienestar cuando quieras. ¿Quieres que lo hagamos?"
    )


MENSAJE_CRISIS = mensaje_crisis()


def _sin_tildes(texto: str) -> str:
    base = unicodedata.normalize("NFD", texto.lower())
    plano = "".join(c for c in base if unicodedata.category(c) != "Mn")
    return re.sub(r"([a-z])\1+", r"\1", plano)  # tolera letras repetidas por error de tipeo


def detectar_crisis(texto: str) -> bool:
    return bool(_PATRON.search(_sin_tildes(texto)))
