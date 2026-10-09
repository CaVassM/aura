"""La comprobación de «¿la persona dijo días y canal?» es laxa pero no se deja engañar por «por la mañana»."""

import pytest

from agente.entrada import dijo_canal, dijo_dias, faltantes


@pytest.mark.parametrize(
    "texto",
    ["puedo lunes y miercoles", "el Miércoles", "mañana", "hoy mismo", "pasado mañana", "cualquier día", "entre semana",
     "los fines de semana", "esta semana", "da igual el día", "SÁBADO"],
)
def test_reconoce_dias(texto):
    assert dijo_dias([texto])


@pytest.mark.parametrize(
    "texto",
    ["Que servicios existen?", "por la mañana", "en la mañana", "de la mañana", "desde las 10", "me siento mal", "marzo"],
)
def test_no_confunde_la_manana_con_un_dia(texto):
    assert not dijo_dias([texto])


@pytest.mark.parametrize(
    "texto",
    ["por videollamada", "Teléfono", "presencial", "por zoom", "en persona", "da igual", "cualquiera", "todo es digital"],
)
def test_reconoce_canal(texto):
    assert dijo_canal([texto])


def test_sin_pistas_no_hay_canal():
    assert not dijo_canal(["puedo lunes y miércoles desde las 10am hasta las 12"])


def test_los_datos_pueden_venir_en_mensajes_distintos():
    assert faltantes(["puedo el lunes"]) == ["el canal (videollamada, teléfono o presencial)"]
    assert faltantes(["puedo el lunes", "por videollamada"]) == []
    assert len(faltantes(["me siento mal"])) == 2
