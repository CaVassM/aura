import pytest

from agente.crisis import MENSAJE_CRISIS, detectar_crisis, mensaje_crisis


@pytest.mark.parametrize(
    "texto",
    [
        "A veces pienso en quitarme la vida",
        "no quiero seguir viviendo",
        "me quiero hacer dano",
        "Me quiero hacer daño",
        "ya no l enecunetro sentido a nada, quisiera desaparecer",
        "quiero morirme",
        "pienso en el suicidio",
        "no quiero estar viva",
        "he pensado en terminar con todo",
    ],
)
def test_detecta_senales_de_crisis(texto):
    assert detectar_crisis(texto)


@pytest.mark.parametrize(
    "texto",
    [
        "Me van a matar los parciales, estoy muerta de sueño",
        "ya no le encuentro sentido a mi carrera",
        "quiero hacer desaparecer el estrés",
        "necesito cortarme el pelo",
        "estoy agobiado con la universidad",
        "mi cita desapareció",
    ],
)
def test_no_confunde_exageraciones_con_crisis(texto):
    assert not detectar_crisis(texto)


def test_el_mensaje_fijo_no_nombra_lineas_reales_pero_se_puede_configurar():
    assert "emergencia" in MENSAJE_CRISIS and "puedo brindarte" in MENSAJE_CRISIS
    assert not any(n in MENSAJE_CRISIS for n in ("113", "MINSA", "Perú"))
    assert "Línea Aethera 800" in mensaje_crisis("la Línea Aethera 800")
