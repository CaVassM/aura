"""Comprueba que la persona dijo de verdad los datos con los que el modelo quiere buscar.

Un modelo pequeño tiende a rellenar días o canal que nadie mencionó. Estas comprobaciones son
deliberadamente laxas (basta una mención, incluso «da igual» o «cualquier día»): solo frenan
la búsqueda cuando no hay ninguna pista, y el error le dice al modelo qué preguntar.
"""

import re
import unicodedata


def _colapsar(texto: str) -> str:
    """«iguual» → «igual», «llamada» → «lamada»: tolera letras repetidas por error. Se aplica al texto y a los patrones."""
    return re.sub(r"([a-z])\1+", r"\1", texto)


_DIAS = re.compile(_colapsar(
    r"\b(lunes|martes|miercoles|jueves|viernes|sabado|domingo|hoy|pasado manana|"
    r"cualquier dia|todos los dias|cada dia|toda la semana|entre semana|fin(es)? de semana|"
    r"(esta|la proxima|la otra|proxima) semana|dias? de semana|dia(s)? que (sea|haya|quieras)|"
    r"(da|me da) igual (el|los) dias?|no importa (el|los) dias?|sin preferencia)\b"
    r"|(?<!la )(?<!las )(?<!de la )\bmanana\b"
    r"|\b(el |para el |del )?\d{1,2} de (enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|setiembre|octubre|noviembre|diciembre)\b"
    r"|\b(para |dia |el )\d{1,2}\b(?!:)"
))
_CANALES = re.compile(_colapsar(
    r"\b(videollamada|video|virtual|online|en linea|zoom|meet|teams|digital|remot[oa]|"
    r"telefono|telefonic[oa]|llamada|celular|whatsapp|"
    r"presencial|presenciales|en persona|cara a cara|campus|"
    r"cualquier canal|cualquiera|cualquier modalidad|da igual|me da igual|me da lo mismo|"
    r"no importa|indistinto|lo que (haya|sea)|todo digital)\b"
))
_CANCELAR = re.compile(_colapsar(
    r"\b(cancel\w*|anul\w*|elimin\w*|borr\w*|dar de baja|deshaz\w*|deshac\w*|"
    r"ya no (la |lo )?(quiero|necesito)|no (la |lo )?quiero (mas|ya)|no voy a (ir|asistir|poder))"
))
_AFIRMA = re.compile(_colapsar(
    r"^\W*(si|claro|ok|okay|dale|vale|de acuerdo|confirmo|por favor|afirmativo|correcto|exacto|hazlo|adelante|sip)\b"
))


def _plano(texto: str) -> str:
    base = unicodedata.normalize("NFD", texto.lower())
    return _colapsar("".join(c for c in base if unicodedata.category(c) != "Mn"))


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


_ACEPTA_LOTE = re.compile(
    _colapsar(r"\b(entr\w*|acept\w*|quiero|anot\w*|apunt\w*|pon\w*|inscrib\w*|meta\w*)\b.*\blote\b")
)
_NEGATIVA = re.compile(r"^\W*(no|nunca|mejor no)\b")


def acepta_lote(mensaje: str, ultima_respuesta: str) -> bool:
    """¿La persona aceptó entrar al lote? Nombrándolo («quiero entrar al lote») o con un «sí» a una pregunta del
    agente que hablaba del lote. Un «no» al comienzo lo niega."""
    plano = _plano(mensaje)
    if _NEGATIVA.search(plano):
        return False
    if _ACEPTA_LOTE.search(plano):
        return True
    return "lote" in _plano(ultima_respuesta) and bool(_AFIRMA.search(plano))


def confirma_cancelacion(mensaje: str, ultima_respuesta: str) -> bool:
    """¿La persona pidió cancelar en este mensaje, o respondió que sí a una pregunta de cancelar?

    Evita que el modelo cancele porque la persona solo comentó o dudó («ya lo agendaste», «sabes mejor no»).
    """
    plano = _plano(mensaje)
    if _CANCELAR.search(plano):
        return True
    return "cancel" in _plano(ultima_respuesta) and bool(_AFIRMA.search(plano))


_ASISTENCIA = re.compile(_colapsar(
    r"\b(asistencia|inasistencia\w*|ausencia\w*|faltas|faltado|faltando|faltar a|faltare a|falte a|"
    r"no (he )?(ido|asistido|voy|fui) a (las )?(clase|clases|mis clases|la universidad)|"
    r"perdido (muchas |varias |bastantes )?clases|dejado de ir a)"
))


def menciona_asistencia(mensaje: str) -> bool:
    """¿La persona habló de su asistencia a clases en este mensaje? Frena que el modelo consulte ese dato por su cuenta."""
    return bool(_ASISTENCIA.search(_plano(mensaje)))
