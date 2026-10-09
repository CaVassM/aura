"""Entradas desordenadas de un LLM: se normalizan, o fallan con un mensaje que explica cómo corregir."""

import json

import pytest

from aura.herramientas.estado_agenda import AgendaViva
from aura.herramientas.esquemas import esquemas_herramientas
from aura.herramientas.herramientas import HerramientasAgente

BASE = {
    "estudiante_id": "T1",
    "motivo": "academic_pressure",
    "distrito": "DIST_GAIA",
    "grupo": "diurno",
    "franjas": [{"dia": "Tue", "desde": "09:00", "hasta": "18:00"}],
    "canales_aceptables": ["digital", "phone"],
}


@pytest.fixture(scope="module")
def agenda():
    return AgendaViva()


@pytest.fixture()
def herramientas(agenda):
    return HerramientasAgente(agenda)


def test_acepta_solicitud_como_texto_json(herramientas):
    r = herramientas.ejecutar("proponer_opciones", json.dumps({"solicitud": json.dumps(BASE), "k": "2"}))
    assert len(r["opciones"]) == 2


@pytest.mark.parametrize(
    "cambio",
    [
        {"canales_aceptables": "digital"},
        {"canales_aceptables": "videollamada, teléfono"},
        {"canales_aceptables": ["Videollamada"]},
        {"franjas": [{"dia": "martes", "desde": "9:00", "hasta": "18:00"}]},
        {"franjas": [{"dia": "Martes", "desde": "09:00", "hasta": "18:00"}]},
        {"franjas": {"dia": "Tuesday", "desde": "09:00", "hasta": "18:00"}},
        {"distrito": "dist_gaia"},
        {"grupo": "Diurno"},
    ],
)
def test_normaliza_variantes_razonables(herramientas, cambio):
    r = herramientas.proponer_opciones({**BASE, **cambio}, 1)
    assert r["opciones"], r


@pytest.mark.parametrize(
    "cambio, pista",
    [
        ({"motivo": "estres"}, "academic_pressure"),
        ({"distrito": "DIST_X"}, "DIST_GAIA"),
        ({"canales_aceptables": ["carta"]}, "in_person"),
        ({"canales_aceptables": []}, "canales_aceptables"),
        ({"franjas": [{"dia": "Tue", "desde": "18:00", "hasta": "09:00"}]}, "anterior"),
        ({"franjas": [{"dia": "Xyz", "desde": "09:00", "hasta": "18:00"}]}, "Mon, Tue"),
        ({"franjas": [{"dia": "Tue", "desde": "nueve", "hasta": "18:00"}]}, "HH:MM"),
        ({"grupo": "vespertino"}, "diurno"),
        ({"fecha_solicitud": "ayer"}, "AAAA-MM-DD"),
    ],
)
def test_errores_dicen_como_corregir(herramientas, cambio, pista):
    r = herramientas.proponer_opciones({**BASE, **cambio}, 1)
    assert r["opciones"] == [] and r["motivo_vacio"] == "solicitud_invalida"
    assert pista in r["detalle"]


def test_sin_cupos_ofrece_sugerencia(herramientas):
    sin_cupos = {**BASE, "franjas": [{"dia": "Sun", "desde": "03:00", "hasta": "04:00"}]}
    r = herramientas.proponer_opciones(sin_cupos, 3)
    assert r["motivo_vacio"] == "sin_cupos_compatibles" and r["sugerencia"]


def test_opciones_incluyen_dia_y_canal_en_espanol(herramientas):
    opcion = herramientas.proponer_opciones(BASE, 1)["opciones"][0]
    assert opcion["dia_semana"] == "martes"
    assert opcion["canal_label"] in {"Videollamada", "Teléfono"}


def test_argumentos_malos_no_lanzan(herramientas):
    assert herramientas.ejecutar("reservar", "no es json")["error"] == "argumentos_invalidos"
    assert herramientas.ejecutar("reservar", {"estudiante_id": "A"})["error"] == "argumentos_invalidos"


def test_reservar_distingue_opcion_invalida_de_cupo_tomado():
    h = HerramientasAgente(AgendaViva())
    assert h.reservar("A", "inventada")["error"] == "opcion_invalida"
    assert h.reservar("A", "C0000001|telepatia")["error"] == "opcion_invalida"
    opcion = h.proponer_opciones(BASE, 1)["opciones"][0]["opcion_id"]
    assert h.reservar("A", opcion)["ok"]
    assert h.reservar("B", opcion)["error"] == "cupo_ya_tomado"


def test_solo_el_dueno_cancela():
    h = HerramientasAgente(AgendaViva())
    opcion = h.proponer_opciones(BASE, 1)["opciones"][0]["opcion_id"]
    cita = h.reservar("A", opcion)["cita"]["cita_id"]
    assert h.cancelar_cita(cita, "B") == {"ok": False, "error": "cita_no_encontrada"}
    assert h.cancelar_cita(cita, "A")["ok"]


def test_esquemas_cierran_los_valores_posibles(agenda):
    esquemas = {e["name"]: e for e in esquemas_herramientas(["DIST_GAIA"], ["academic_pressure"])}
    solicitud = esquemas["proponer_opciones"]["parameters"]["properties"]["solicitud"]["properties"]
    assert solicitud["distrito"]["enum"] == ["DIST_GAIA"]
    assert solicitud["motivo"]["enum"] == ["academic_pressure"]
    assert solicitud["canales_aceptables"]["items"]["enum"] == ["digital", "phone", "in_person"]
    assert "enum" in solicitud["franjas"]["items"]["properties"]["dia"]
    json.dumps(esquemas, ensure_ascii=False)
