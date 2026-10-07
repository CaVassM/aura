"""Perfiles de estudiante del protocolo D5 convertidos en solicitudes del motor."""

from datetime import date, time

from .modelos import Franja, Solicitud


def franjas_de_perfil(perfil: dict) -> tuple[Franja, ...]:
    """Traduce la modalidad declarada a las ventanas horarias del protocolo D5."""
    if perfil["modalidad"] == "day":
        desde, hasta = time(9), time(18)
    elif perfil["trabaja"]:
        desde, hasta = time(19), time(21)
    else:
        desde, hasta = time(17), time(21)
    return tuple(Franja(dia, desde, hasta) for dia in range(5))


def crear_solicitud(
    conversacion: dict, perfil: dict, servicio_d5, ideal: str, hoy: date
) -> Solicitud:
    """Construye la solicitud de prueba usando el distrito del servicio de D5."""
    canales = (
        ("digital",)
        if perfil["prefiere_escrito"]
        else ("digital", "phone", "in_person")
    )
    grupo = "diurno" if perfil["modalidad"] == "day" else "nocturno"
    distrito = servicio_d5.distrito if servicio_d5 else "UNKNOWN"
    return Solicitud(
        id=conversacion["conversation_id"],
        servicio_ideal=ideal,
        distrito=distrito,
        franjas=franjas_de_perfil(perfil),
        canales_aceptables=canales,
        fecha_solicitud=hoy,
        grupo=grupo,
    )
