"""Siembra de la demo: determinismo, requisitos y perfil D5."""

from dataclasses import replace
from datetime import date, timedelta

import pytest

from aura.datos.perfiles import crear_solicitud
from app.services.siembra_service import crear_estado_sembrado
from app.settings import Settings


def test_siembra_es_determinista(estado_sembrado, settings):
    otra = crear_estado_sembrado(settings)
    assert otra.motor.citas() == estado_sembrado.motor.citas()
    assert otra.desencuentros == estado_sembrado.desencuentros


def test_ningun_pedido_es_anterior_a_la_semana_de_la_demo(estado_sembrado):
    """Los pedidos base y los extra quedan fechados dentro de la semana de la demo."""
    lunes = estado_sembrado.hoy - timedelta(days=estado_sembrado.hoy.weekday())
    esc = estado_sembrado.escenario
    fechas = [s.fecha_solicitud for s in estado_sembrado.motor.demanda_demo(esc["semilla"], esc["factor"])]
    fechas += [date.fromisoformat(d["fecha"]) for d in estado_sembrado.desencuentros]
    assert min(fechas) >= lunes and max(fechas) <= estado_sembrado.hoy


def test_los_desencuentros_los_decide_el_motor(estado_sembrado):
    """Todo desencuentro conserva motivo y canales de una solicitud real, sin escribirse a mano."""
    assert estado_sembrado.desencuentros
    for d in estado_sembrado.desencuentros:
        assert d["motivo"] and d["canales_aceptables"] and d["grupo"] == "nocturno"


def test_vespertino_trabaja_usa_la_proporcion_configurada(settings):
    estado = crear_estado_sembrado(settings, "x1")
    p = estado.escenario["proporcion_vespertino_trabaja"]
    base, extras = estado.siembra["solicitudes_base"], estado.siembra["extras_vespertino_trabaja"]
    assert p > 0 and extras / (base + extras) == pytest.approx(p, abs=0.01)


def test_siembra_sin_d2_falla_con_mensaje_claro(tmp_path, settings):
    from app.repositories.app_state import construir_estado
    from app.services.siembra_service import sembrar

    estado = construir_estado(settings)
    estado.settings = replace(settings, data_dir=tmp_path)
    with pytest.raises(RuntimeError, match="D2"):
        sembrar(estado)


def test_perfil_vespertino_que_trabaja_es_19_a_21():
    perfil = {"modalidad": "evening", "trabaja": True, "prefiere_escrito": False}
    solicitud = crear_solicitud({"conversation_id": "X"}, perfil, None, "counseling", date(2026, 9, 28))
    assert solicitud.grupo == "nocturno"
    assert {(f.hora_inicio.hour, f.hora_fin.hour) for f in solicitud.franjas} == {(19, 21)}
    assert solicitud.distrito == "UNKNOWN"
