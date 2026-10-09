"""Normaliza y valida las preferencias que entrega un LLM antes de llegar al motor.

Un modelo pequeño suele mandar la solicitud como texto JSON, los canales como una sola
cadena, los días en español o las horas como «9:00». Aquí se acepta lo razonable y, cuando
algo no se puede usar, el error dice qué valores son válidos para que el modelo corrija.
"""

import json
import re
import unicodedata
from datetime import date, time

from ..motor.datos import Franja, Solicitud

DIAS = {
    "mon": 0, "monday": 0, "lun": 0, "lunes": 0,
    "tue": 1, "tuesday": 1, "mar": 1, "martes": 1,
    "wed": 2, "wednesday": 2, "mie": 2, "miercoles": 2,
    "thu": 3, "thursday": 3, "jue": 3, "jueves": 3,
    "fri": 4, "friday": 4, "vie": 4, "viernes": 4,
    "sat": 5, "saturday": 5, "sab": 5, "sabado": 5,
    "sun": 6, "sunday": 6, "dom": 6, "domingo": 6,
}
CANALES = ("digital", "phone", "in_person")
_ALIAS_CANAL = {
    "videollamada": "digital", "video": "digital", "virtual": "digital", "online": "digital",
    "telefono": "phone", "llamada": "phone", "telefonico": "phone",
    "presencial": "in_person", "en persona": "in_person",
}
GRUPOS = ("diurno", "nocturno")
_HORA = re.compile(r"^(\d{1,2})(?::(\d{2}))?(?::\d{2})?$")


def _plano(texto) -> str:
    """Minúsculas y sin tildes, para comparar entradas escritas de varias formas."""
    base = unicodedata.normalize("NFD", str(texto).strip().lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


def como_diccionario(valor, nombre: str) -> dict:
    """Acepta un dict o un texto JSON que lo contenga."""
    if isinstance(valor, str):
        try:
            valor = json.loads(valor)
        except json.JSONDecodeError as error:
            raise ValueError(f"`{nombre}` debe ser un objeto JSON: {error}") from error
    if not isinstance(valor, dict):
        raise ValueError(f"`{nombre}` debe ser un objeto con las preferencias de la persona")
    return valor


def _lista(valor, nombre: str) -> list:
    if isinstance(valor, str):
        texto = valor.strip()
        if texto.startswith("["):
            try:
                valor = json.loads(texto)
            except json.JSONDecodeError:
                valor = [texto]
        else:
            valor = [parte for parte in re.split(r"[,;/]|\sy\s", texto) if parte.strip()]
    if isinstance(valor, dict):
        valor = [valor]
    if not isinstance(valor, (list, tuple)) or not valor:
        raise ValueError(f"`{nombre}` debe ser una lista con al menos un elemento")
    return list(valor)


def indice_dia(dia) -> int:
    texto = _plano(dia)
    if texto.isdigit() and 0 <= int(texto) <= 6:
        return int(texto)
    if texto in DIAS:
        return DIAS[texto]
    raise ValueError(f"Día no válido: {dia!r}. Usa Mon, Tue, Wed, Thu, Fri, Sat o Sun")


def hora(valor) -> time:
    coincide = _HORA.match(str(valor).strip())
    if not coincide:
        raise ValueError(f"Hora no válida: {valor!r}. Usa el formato HH:MM, p. ej. 09:00")
    horas, minutos = int(coincide.group(1)), int(coincide.group(2) or 0)
    if horas > 23 or minutos > 59:
        raise ValueError(f"Hora fuera de rango: {valor!r}")
    return time(horas, minutos)


def franjas(valor) -> tuple[Franja, ...]:
    resultado = []
    for franja in _lista(valor, "franjas"):
        franja = como_diccionario(franja, "franjas[]")
        faltan = [c for c in ("dia", "desde", "hasta") if c not in franja]
        if faltan:
            raise ValueError(f"Cada franja necesita dia, desde y hasta (falta: {', '.join(faltan)})")
        desde, hasta = hora(franja["desde"]), hora(franja["hasta"])
        if desde >= hasta:
            raise ValueError(f"En la franja, `desde` ({desde:%H:%M}) debe ser anterior a `hasta` ({hasta:%H:%M})")
        resultado.append(Franja(indice_dia(franja["dia"]), desde, hasta))
    return tuple(resultado)


def canales(valor) -> tuple[str, ...]:
    resultado = []
    for canal in _lista(valor, "canales_aceptables"):
        plano = _plano(canal).replace(" ", "_")
        plano = _ALIAS_CANAL.get(_plano(canal), plano)
        if plano not in CANALES:
            raise ValueError(
                f"Canal no válido: {canal!r}. Usa digital (videollamada), phone (teléfono) o in_person (presencial)"
            )
        if plano not in resultado:
            resultado.append(plano)
    return tuple(resultado)


def distrito(valor, distritos: set[str] | None) -> str:
    texto = str(valor).strip().upper()
    if distritos is not None and texto not in distritos:
        raise ValueError(f"Distrito no válido: {valor!r}. Distritos de la red: {', '.join(sorted(distritos))}")
    return texto


def convertir_solicitud(
    entrada, hoy: date, tablas: dict, distritos: set[str] | None = None
) -> tuple[Solicitud, str]:
    """Valida las preferencias y traduce el motivo a servicio ideal con `tablas.yaml`."""
    entrada = como_diccionario(entrada, "solicitud")
    motivos = tablas["motivo_a_servicio"]
    motivo = str(entrada.get("motivo", "")).strip()
    tipo_ideal = motivos.get(motivo)
    if tipo_ideal is None:
        raise ValueError(f"Motivo no válido: {motivo!r}. Motivos disponibles: {', '.join(motivos)}")
    for campo in ("estudiante_id", "distrito", "franjas", "canales_aceptables"):
        if not entrada.get(campo):
            raise ValueError(f"Falta el campo obligatorio `{campo}`")
    grupo = _plano(entrada.get("grupo") or "diurno")
    if grupo not in GRUPOS:
        raise ValueError(f"Grupo no válido: {entrada.get('grupo')!r}. Usa diurno o nocturno")
    try:
        fecha = date.fromisoformat(str(entrada.get("fecha_solicitud") or hoy.isoformat()))
    except ValueError as error:
        raise ValueError("`fecha_solicitud` debe tener formato AAAA-MM-DD") from error
    solicitud = Solicitud(
        str(entrada["estudiante_id"]),
        tipo_ideal,
        distrito(entrada["distrito"], distritos),
        franjas(entrada["franjas"]),
        canales(entrada["canales_aceptables"]),
        fecha,
        grupo,
        motivo,
    )
    return solicitud, tipo_ideal
