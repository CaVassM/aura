"""Comprueba que la persona dijo de verdad los datos con los que el modelo quiere buscar.

Un modelo pequeño tiende a rellenar días o canal que nadie mencionó. Estas comprobaciones son
deliberadamente laxas (basta una mención, incluso «da igual» o «cualquier día»): solo frenan
la búsqueda cuando no hay ninguna pista, y el error le dice al modelo qué preguntar.
"""

import re
import unicodedata

_DIAS = re.compile(
    r"\b(lunes|martes|miercoles|jueves|viernes|sabado|domingo|hoy|pasado manana|"
    r"cualquier dia|todos los dias|cada dia|toda la semana|entre semana|fin(es)? de semana|"
    r"(esta|la proxima|la otra|proxima) semana|dias? de semana|dia(s)? que (sea|haya|quieras)|"
    r"(da|me da) igual (el|los) dias?|no importa (el|los) dias?|sin preferencia)\b"
    r"|(?<!la )(?<!las )(?<!de la )\bmanana\b"
)
_CANALES = re.compile(
    r"\b(videollamada|video|virtual|online|en linea|zoom|meet|teams|digital|remot[oa]|"
    r"telefono|telefonic[oa]|llamada|celular|whatsapp|"
    r"presencial|presenciales|en persona|cara a cara|campus|"
    r"cualquier canal|cualquiera|cualquier modalidad|da igual|me da igual|me da lo mismo|"
    r"no importa|indistinto|lo que (haya|sea)|todo digital)\b"
)


def _plano(texto: str) -> str:
    base = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


def dijo_dias(textos: list[str]) -> bool:
    return any(_DIAS.search(_plano(t)) for t in textos)


def dijo_canal(textos: list[str]) -> bool:
    return any(_CANALES.search(_plano(t)) for t in textos)


def faltantes(textos: list[str]) -> list[str]:
    """Qué datos de la búsqueda la persona aún no ha dicho (`días`, `canal`)."""
    falta = []
    if not dijo_dias(textos):
        falta.append("los días en que puede asistir")
    if not dijo_canal(textos):
        falta.append("el canal (videollamada, teléfono o presencial)")
    return falta
