"""Siembra de la demo: simula la demanda de la semana con el motor en modo directo."""

import random
from dataclasses import replace
from datetime import timedelta
from types import SimpleNamespace

from aura.datos.perfiles import crear_solicitud

from ..models import Cita
from ..repositories.app_state import AppState, construir_estado
from .etiquetas import Etiquetas

PERFIL_VESPERTINO_TRABAJA = {
    "modalidad": "evening",
    "trabaja": True,
    "prefiere_escrito": False,
}


def _vespertino_trabaja(estado: AppState, base: list) -> list:
    """Solicitudes extra de vespertino que trabaja (franja 19–21), con el perfil D5.

    Son un supuesto de simulación: `proporcion` es la parte del total de solicitudes.
    Motivo y servicio ideal se copian de solicitudes de la semana; el distrito sale de D6.
    El desencuentro, si lo hay, lo decide el motor.
    """
    proporcion = estado.escenario["proporcion_vespertino_trabaja"]
    if not 0 <= proporcion < 1:
        raise ValueError("demo.proporcion_vespertino_trabaja debe estar en [0, 1)")
    cantidad = round(len(base) * proporcion / (1 - proporcion))
    rng = random.Random(estado.escenario["semilla"])
    distritos = sorted({s["distrito"] for s in estado.motor.servicios()})
    lunes = estado.hoy - timedelta(days=estado.hoy.weekday())  # semana de la demo
    extras = []
    for i in range(cantidad):
        plantilla = rng.choice(base)
        solicitud = crear_solicitud(
            {"conversation_id": f"DEMO_VESP_{i + 1:03d}"},
            PERFIL_VESPERTINO_TRABAJA,
            SimpleNamespace(distrito=rng.choice(distritos)),
            plantilla.servicio_ideal,
            lunes + timedelta(days=rng.randrange(5)),
        )
        extras.append(replace(solicitud, motivo=plantilla.motivo))
    return extras


def sembrar(estado: AppState) -> AppState:
    """Deja en `estado` la semana simulada: citas ocupando cupos y desencuentros del motor.

    Requiere D2 (la demanda sale de su semana mediana); sin D2 falla con un mensaje claro.
    """
    d2 = estado.settings.data_dir / "D2_support_services.csv"
    if not d2.exists():
        raise RuntimeError(
            f"La siembra de la demo requiere D2 y no se encontró {d2}. "
            "Define AURA_DATA_DIR con la carpeta del Data Pack."
        )
    with estado.lock:
        esc = estado.escenario
        base = estado.motor.demanda_demo(esc["semilla"], esc["factor"])
        extras = _vespertino_trabaja(estado, base)
        etiquetas = Etiquetas(estado.tablas)
        for resultado in estado.motor.atender_lote(base + extras):
            if resultado["estado"] == "reservada":
                estado.citas.add(Cita.desde_comprobante(resultado["cita"], etiquetas.tipo))
        estado.siembra = {
            "solicitudes_base": len(base),
            "extras_vespertino_trabaja": len(extras),
        }
    return estado


def crear_estado_sembrado(
    settings, escenario: str | None = None, semilla: int | None = None
) -> AppState:
    """Construye el estado de un escenario y lo siembra."""
    return sembrar(construir_estado(settings, escenario, semilla))
