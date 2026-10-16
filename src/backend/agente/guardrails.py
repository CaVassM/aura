"""Guardrails deterministas que corren ANTES del modelo (junto a `crisis.py`).

Las reglas viven aquí y no en el prompt: un modelo pequeño las olvida o las reinterpreta. Si un mensaje cae en uno de estos
casos, la respuesta es un texto fijo y el modelo ni se invoca. Ninguno es una crisis (eso lo decide `crisis.py`, que corre
primero): la conversación sigue su flujo normal en el siguiente mensaje.

- Límite clínico: pedir un medicamento o un diagnóstico («¿qué medicamento tomo?», «creo que tengo depresión»).
- Datos de profesionales: pedir el número o el contacto de un psicólogo, psiquiatra, etc.
"""

import re
import unicodedata
from dataclasses import dataclass

MENSAJE_LIMITE_CLINICO = (
    "No puedo diagnosticar ni recomendar medicamentos; eso lo ve un profesional. "
    "Si quieres, te ayudo a agendar con consejería."
)
MENSAJE_DATOS_PROFESIONALES = (
    "Solo puedo mostrarte los servicios de la red de bienestar y ayudarte a agendar una cita en ellos; no tengo números "
    "ni datos de contacto de profesionales. Si quieres, te ayudo a agendar."
)


@dataclass(frozen=True)
class Guardrail:
    tipo: str  # limite_clinico | datos_profesionales
    texto: str


def _plano(texto: str) -> str:
    base = unicodedata.normalize("NFD", texto.lower())
    plano = "".join(c for c in base if unicodedata.category(c) != "Mn")
    return re.sub(r"([a-z])\1+", r"\1", plano)  # tolera letras repetidas por error de tipeo


def _patron(expresion: str) -> re.Pattern:
    return re.compile(re.sub(r"([a-z])\1+", r"\1", expresion))


_MEDICAMENTO = _patron(
    r"\b(medicament\w*|medicin\w*|pastilla\w*|farmac\w*|antidepresiv\w*|ansiolitic\w*|somnifer\w*|"
    r"sertralina|fluoxetina|clonazepam|alprazolam|diazepam|ibuprofeno|paracetamol|melatonina|"
    r"dosis|recet(a|ar|arme|en|o|aron)\b)"
)
_CONDICION = _patron(
    r"\b(depresion|depresivo|ansiedad|bipolar\w*|trastorno\w*|tdah|adhd|esquizofreni\w*|autismo|toc|fobia\w*|"
    r"panico|anorexia|bulimia|estres postraumatico|burnout|insomnio cronico)\b"
)
_AUTODIAGNOSTICO = _patron(
    r"\b((creo|pienso|siento|sospecho|supongo|me parece|parece|dicen|dijeron|creen) que (tengo|soy|padezco|sufro|tendre|estoy con)|"
    r"sera que (tengo|soy|sufro)|padezco|sufro de|diagnostic\w*|(soy|sere) (bipolar\w*|autista|tdah|adhd)|"
    r"tengo (depresion|bipolaridad|esquizofreni\w*|tdah|adhd|anorexia|bulimia|trastorno\w*|autismo|toc|fobia\w*))\b"
)
_PIDE_DIAGNOSTICO = _patron(r"\bdiagnostic\w*\b")
_QUIERE_CITA =_patron(r"\b(cita|citas|agend\w*|reserv\w*|turno|consejeria|hora para)\b")

_CONTACTO = r"(numero|telefono|celular|contacto|correo|email|e-?mail|direccion|whatsapp|consultorio|nombre)"
_PROFESIONAL = r"(psicolog\w*|psiquiatr\w*|terapeut\w*|consejer[oa]s?|doctor\w*|medic[oa]s?|especialista\w*|profesional\w*)"
_DATOS_PROFESIONAL = _patron(rf"\b{_CONTACTO}\b.{{0,40}}\b{_PROFESIONAL}\b|\b{_PROFESIONAL}\b.{{0,40}}\b{_CONTACTO}\b")


def evaluar(mensaje: str) -> Guardrail | None:
    """El guardrail que aplica a este mensaje, o None si el modelo puede atenderlo."""
    plano = _plano(mensaje)
    if _MEDICAMENTO.search(plano):
        return Guardrail("limite_clinico", MENSAJE_LIMITE_CLINICO)
    # Un autodiagnóstico que además pide agendar («tengo ansiedad por los parciales, quiero una cita…») sí es un pedido de
    # cita: lo atiende el modelo (el prompt le prohíbe diagnosticar). Sin pedido de cita, se responde el límite.
    pide_diagnostico = _PIDE_DIAGNOSTICO.search(plano) or (_CONDICION.search(plano) and _AUTODIAGNOSTICO.search(plano))
    if pide_diagnostico and not _QUIERE_CITA.search(plano):
        return Guardrail("limite_clinico", MENSAJE_LIMITE_CLINICO)
    if _DATOS_PROFESIONAL.search(plano):
        return Guardrail("datos_profesionales", MENSAJE_DATOS_PROFESIONALES)
    return None
