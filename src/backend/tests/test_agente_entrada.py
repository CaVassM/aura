"""La comprobación de «¿la persona dijo días y canal?» es laxa pero no se deja engañar por «por la mañana»."""

import pytest

from agente import entrada
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


@pytest.mark.parametrize("texto", ["Da iguual el canal reealmente", "por videoollamada", "prefiero presenciaal"])
def test_tolera_letras_repetidas_por_error_de_tipeo(texto):
    assert dijo_canal([texto])


@pytest.mark.parametrize(
    "mensaje, ultima, esperado",
    [
        ("Puedes cancelarlo?", "", True),
        ("cancélala por favor", "", True),
        ("ya no quiero la cita", "", True),
        ("anula mi cita", "", True),
        ("sí", "Entendido. ¿Quieres que la cancele?", True),
        ("dale", "¿Te gustaría cancelarla?", True),
        ("sí", "¿Cuál de estas opciones prefieres?", False),  # un «sí» solo vale si se preguntó por cancelar
        ("O sea igual ya lo agendaste", "", False),
        ("Sabes mejor no", "", False),
        ("mejor déjame pensarlo", "", False),
    ],
)
def test_cancelar_exige_pedido_o_confirmacion(mensaje, ultima, esperado):
    from agente.entrada import confirma_cancelacion

    assert confirma_cancelacion(mensaje, ultima) is esperado


@pytest.mark.parametrize(
    "mensaje, ultima, esperado",
    [
        ("sí, cámbiala", "", True),
        ("Reprográmala por esta", "", True),
        ("sí", "Ya tienes una cita de consejería el jueves 26 a las 14:00. ¿Quieres cambiarla por esta?", True),
        ("dale", "¿Quieres cambiarla por esta?", True),
        ("sí", "¿Cuál de estas opciones prefieres?", False),
        ("no, déjala como está", "¿Quieres cambiarla por esta?", False),
        ("no la cambies", "", False),
        ("mmm déjame pensarlo", "¿Quieres cambiarla por esta?", False),
        ("puedo pasado mañana", "¿Quieres cambiarla por esta?", False),
    ],
)
def test_reemplazar_una_cita_exige_confirmacion_clara(mensaje, ultima, esperado):
    from agente.entrada import acepta_reemplazo

    assert acepta_reemplazo(mensaje, ultima) is esperado


@pytest.mark.parametrize("texto", [
    "¿Cómo va mi asistencia?", "He faltado mucho", "tengo muchas inasistencias", "no he ido a clases",
    "llevo muchas faltas en cálculo", "perdido varias clases",
])
def test_menciona_asistencia(texto):
    assert entrada.menciona_asistencia(texto)


@pytest.mark.parametrize("texto", [
    "Tengo parciales", "me falta tiempo", "puedo asistir el miércoles", "por videollamada", "quiero agendar una cita",
])
def test_no_menciona_asistencia(texto):
    assert not entrada.menciona_asistencia(texto)


@pytest.mark.parametrize("texto", ["para el 18 de noviembre", "el 18", "18 de noviembre", "dia 25", "el 3 de diciembre"])
def test_una_fecha_cuenta_como_dia_dicho(texto):
    assert dijo_dias([texto])


@pytest.mark.parametrize("texto", ["Quiero la opción 3 a las 14:00", "tengo 2 exámenes"])
def test_un_numero_suelto_no_es_dia(texto):
    assert not dijo_dias([texto])
