"""Guardrails antes del modelo, llamadas mal formadas, equidad R7 en el chat y reglas que viven en las herramientas."""

import json

import pytest

pytest.importorskip("langchain")
pytest.importorskip("langchain_ollama")

from langchain_core.messages import AIMessage

from agente import guardrails
from agente.agente import SIN_RESPUESTA
from agente.crisis import detectar_crisis
from tests.test_agente_chat import (  # noqa: F401 — `montar` es un fixture
    MSG,
    ModeloGuionado,
    citas_de,
    llamada,
    montar,
    ultimo_resultado,
)

CARRERA = {
    "motivo": "career_concern",
    "franjas": [{"dia": "Wed", "desde": "09:00", "hasta": "18:00"}],
    "canales_aceptables": ["digital"],
    "distrito": "DIST_GAIA",
}


# --- guardrails: capa determinística --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mensaje, esperado",
    [
        ("¿Qué medicamento debería tomar?", "limite_clinico"),
        ("¿Puedo tomar pastillas para dormir?", "limite_clinico"),
        ("Mi psiquiatra me recetó sertralina, ¿la dejo?", "limite_clinico"),
        ("creo que tengo depresión", "limite_clinico"),
        ("Creo que tengo ansiedad", "limite_clinico"),
        ("¿Me pueden diagnosticar?", "limite_clinico"),
        ("Dame el número de un psicólogo", "datos_profesionales"),
        ("¿Tienes el teléfono de algún psiquiatra?", "datos_profesionales"),
        ("pásame el contacto de un terapeuta", "datos_profesionales"),
        ("Tengo parciales, puedo el miércoles por videollamada", None),
        ("Estoy con mucha ansiedad por los parciales, quiero una cita el martes", None),
        ("Tengo ansiedad por los parciales", None),
        ("¿Qué servicios existen?", None),
        ("quiero agendar con consejería", None),
        ("No quiero vivir", None),  # la crisis la decide crisis.py, que corre antes
    ],
)
def test_guardrails_deterministas(mensaje, esperado):
    g = guardrails.evaluar(mensaje)
    assert (g.tipo if g else None) == esperado


def test_el_mensaje_del_limite_clinico_no_tiene_el_error_de_tipeo():
    assert guardrails.MENSAJE_LIMITE_CLINICO == (
        "No puedo diagnosticar ni recomendar medicamentos; eso lo ve un profesional. "
        "Si quieres, te ayudo a agendar con consejería."
    )
    assert "contáalos" not in guardrails.MENSAJE_LIMITE_CLINICO and "contáalos" not in guardrails.MENSAJE_DATOS_PROFESIONALES


def test_la_crisis_sigue_siendo_crisis_y_el_limite_clinico_no():
    assert detectar_crisis("No quiero vivir") and detectar_crisis("A veces pienso en quitarme la vida")
    assert not detectar_crisis("¿Qué medicamento debería tomar?") and not detectar_crisis("creo que tengo depresión")


def test_limite_clinico_responde_sin_llamar_al_modelo_y_no_es_crisis(montar, estado_fresco):
    cliente, modelo = montar(lambda m: AIMessage("no debería llamarse"))
    r = cliente.post("/api/chat", json={"mensaje": "¿Qué medicamento debería tomar?", "estudiante_id": "E1"}).json()
    assert r["respuesta"] == guardrails.MENSAJE_LIMITE_CLINICO
    assert r["alerta_crisis"] is False and r["opciones"] == [] and r["herramientas_usadas"] == []
    assert modelo.llamadas == 0 and citas_de(estado_fresco, "E1") == []


def test_tras_el_limite_clinico_el_flujo_normal_sigue(montar):
    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        return llamada("proponer_opciones", **CARRERA) if r is None else AIMessage(f"Encontré {len(r['opciones'])} opciones.")

    cliente, modelo = montar(guion)
    sid = cliente.post("/api/chat", json={"mensaje": "creo que tengo depresión", "estudiante_id": "E1"}).json()["session_id"]
    r = cliente.post(
        "/api/chat", json={"mensaje": "sí, busca el miércoles por videollamada", "estudiante_id": "E1", "session_id": sid}
    ).json()
    assert r["opciones"] and r["respuesta"].startswith("Encontré")
    historial = cliente.get(f"/api/chat/{sid}", params={"estudiante_id": "E1"}).json()["mensajes"]
    assert [m["rol"] for m in historial] == ["user", "agent", "user", "agent"]


def test_datos_de_profesionales_se_explican_y_se_ofrece_agendar(montar):
    cliente, modelo = montar(lambda m: AIMessage("no debería llamarse"))
    r = cliente.post("/api/chat", json={"mensaje": "dame el número de un psicólogo", "estudiante_id": "E1"}).json()
    assert r["respuesta"] == guardrails.MENSAJE_DATOS_PROFESIONALES and "agendar" in r["respuesta"]
    assert modelo.llamadas == 0 and r["alerta_crisis"] is False


def test_riesgo_inmediato_mantiene_la_tarjeta_de_ayuda(montar):
    cliente, modelo = montar(lambda m: AIMessage("no debería llamarse"))
    r = cliente.post("/api/chat", json={"mensaje": "No quiero vivir", "estudiante_id": "E1"}).json()
    assert r["alerta_crisis"] is True and "emergencia" in r["respuesta"] and modelo.llamadas == 0


# --- llamada a herramienta mal formada: respaldo determinístico ------------------------------------------------------


class ModeloQueFalla(ModeloGuionado):
    """Falla las primeras `fallos` veces con el error que Ollama da por una llamada mal formada."""

    fallos: int = 1

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        if self.llamadas < self.fallos:
            self.llamadas += 1
            raise ValueError("error parsing tool call: raw='{\"name\": \"proponer_opciones\", \"arguments\": {'")
        return super()._generate(messages, stop, run_manager, **kwargs)


def _montar_con(modelo, settings, estado):
    from fastapi.testclient import TestClient

    from agente.agente import AgenteAura
    from app.main import create_app

    return TestClient(create_app(settings, estado, agente=AgenteAura(modelo=modelo)))


def test_llamada_mal_formada_se_reintenta_una_vez_y_el_chat_sigue(settings, estado_fresco, sin_modo_lote):
    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        return llamada("proponer_opciones", **CARRERA) if r is None else AIMessage("Aquí tienes.")

    modelo = ModeloQueFalla(guion=guion, fallos=1)
    with _montar_con(modelo, settings, estado_fresco) as cliente:
        r = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"})
    assert r.status_code == 200 and r.json()["respuesta"] == "Aquí tienes." and r.json()["opciones"]


def test_si_el_reintento_tambien_falla_responde_un_mensaje_seguro_sin_romper_el_chat(settings, estado_fresco):
    modelo = ModeloQueFalla(guion=lambda m: AIMessage("nunca"), fallos=99)
    with _montar_con(modelo, settings, estado_fresco) as cliente:
        r = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"})
        assert r.status_code == 200
        cuerpo = r.json()
        assert cuerpo["respuesta"] == SIN_RESPUESTA and cuerpo["opciones"] == [] and cuerpo["cita"] is None
        # el chat sigue funcionando: la conversación existe y acepta otro mensaje
        otra = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1", "session_id": cuerpo["session_id"]})
        assert otra.status_code == 200
    assert modelo.llamadas == 4  # dos intentos por mensaje


def test_llamada_escrita_como_texto_se_trata_como_mal_formada(settings, estado_fresco, sin_modo_lote):
    escrito = '{"name": "proponer_opciones", "arguments": {"motivo": "career_concern"}}'
    intentos = []

    def guion(mensajes):
        intentos.append(1)
        r = ultimo_resultado(mensajes)
        if r is not None:
            return AIMessage("Aquí tienes.")
        return AIMessage(escrito) if len(intentos) == 1 else llamada("proponer_opciones", **CARRERA)

    modelo = ModeloGuionado(guion=guion)
    with _montar_con(modelo, settings, estado_fresco) as cliente:
        r = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()
    assert r["respuesta"] == "Aquí tienes." and r["opciones"]
    assert escrito not in r["respuesta"]


def test_llamada_escrita_como_texto_dos_veces_no_llega_a_la_persona(settings, estado_fresco):
    modelo = ModeloGuionado(guion=lambda m: AIMessage('<tool_call>{"name": "reservar_cita"}</tool_call>'))
    with _montar_con(modelo, settings, estado_fresco) as cliente:
        r = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()
    assert r["respuesta"] == SIN_RESPUESTA and "tool_call" not in r["respuesta"]


def test_un_fallo_tras_una_reserva_no_la_repite(settings, estado_fresco, sin_modo_lote):
    """Si ya se reservó en este turno y el modelo falla después, no se reintenta: no se duplica la cita."""
    pasos = []

    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        humanos = [m for m in mensajes if m.type == "human"]
        if r is None and len(humanos) == 1:
            return llamada("proponer_opciones", **CARRERA)
        if r is None:
            return llamada("reservar_cita", numero=1)
        if "cita" in r:
            pasos.append("reservada")
            raise ValueError("error parsing tool call")
        return AIMessage("Estas son las opciones.")

    modelo = ModeloGuionado(guion=guion)
    with _montar_con(modelo, settings, estado_fresco) as cliente:
        sid = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()["session_id"]
        r = cliente.post("/api/chat", json={"mensaje": "la primera", "estudiante_id": "E1", "session_id": sid}).json()
    assert pasos == ["reservada"] and len(citas_de(estado_fresco, "E1")) == 1
    assert r["cita"] and "Listo, tu cita quedó confirmada" in r["respuesta"]


# --- confirmación con la línea del canal ----------------------------------------------------------------------------


def test_la_confirmacion_lleva_la_linea_del_canal_para_el_modelo_y_para_el_frontend(montar):
    vistos = []

    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        humanos = [m for m in mensajes if m.type == "human"]
        if r is None:
            return llamada("proponer_opciones", **CARRERA) if len(humanos) == 1 else llamada("reservar_cita", numero=1)
        vistos.append(r)
        return AIMessage("Listo.")

    cliente, _ = montar(guion)
    sid = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()["session_id"]
    r = cliente.post("/api/chat", json={"mensaje": "la primera", "estudiante_id": "E1", "session_id": sid}).json()
    linea = "El servicio te enviará el enlace a tu correo institucional antes de la cita."
    assert r["cita"]["aviso_canal"] == linea
    assert vistos[-1]["cita"]["aviso_canal"] == linea and "aviso_canal" in vistos[-1]["indicacion"]


# --- R7 en la conversación ------------------------------------------------------------------------------------------


def guion_r7(acciones):
    """Un turno por mensaje de la persona: `acciones[n]` es lo que hace el modelo en el mensaje n (0, 1, 2…)."""

    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        humanos = [m for m in mensajes if m.type == "human"]
        if r is not None:
            return AIMessage(r.get("mensaje") or r.get("detalle") or "ok")
        nombre, args = acciones[len(humanos) - 1]
        return llamada(nombre, **args)

    return guion


def test_r7_en_el_chat_ofrece_cambiar_la_cita_y_solo_la_cambia_si_la_persona_confirma(montar, estado_fresco):
    acciones = [
        ("proponer_opciones", CARRERA),
        ("reservar_cita", {"numero": 1}),
        ("proponer_opciones", {**CARRERA, "k": 2}),  # otra búsqueda, mismo tipo
        ("reservar_cita", {"numero": 1}),  # choca con la cita que ya tiene
        ("reservar_cita", {"numero": 1, "reemplazar": True}),  # «no, déjala» → el modelo insiste: la herramienta se niega
        ("reservar_cita", {"numero": 1, "reemplazar": True}),  # «sí, cámbiala»
    ]
    cliente, _ = montar(guion_r7(acciones))
    sid = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()["session_id"]

    def decir(texto):
        return cliente.post("/api/chat", json={"mensaje": texto, "estudiante_id": "E1", "session_id": sid}).json()

    primera = decir("la primera")["cita"]
    assert primera and len(citas_de(estado_fresco, "E1")) == 1
    decir("busca otra vez, quiero otra cita de orientación vocacional el miércoles por videollamada")
    choque = decir("la primera")
    assert choque["cita"] is None
    assert choque["ya_tiene_cita"]["mensaje"].startswith("Ya tienes una cita de orientación vocacional el ")
    assert choque["ya_tiene_cita"]["mensaje"].endswith("¿Quieres cambiarla por esta?")
    assert choque["ya_tiene_cita"]["cita"]["id"] == primera["id"]
    assert choque["respuesta"] == choque["ya_tiene_cita"]["mensaje"]  # el modelo muestra el mensaje tal cual
    assert len(citas_de(estado_fresco, "E1")) == 1  # nada cambió

    rechaza = decir("no, déjala como está")
    assert rechaza["cita"] is None and "falta_confirmacion" not in rechaza["respuesta"] and len(citas_de(estado_fresco, "E1")) == 1
    confirma = decir("sí, cámbiala")
    assert confirma["cita"] and confirma["cita"]["id"] != primera["id"]
    mias = [c for c in cliente.get("/api/appointments", params={"estudiante_id": "E1"}).json()]
    assert {c["id"]: c["estado"] for c in mias} == {primera["id"]: "cancelada", confirma["cita"]["id"]: "confirmada"}
    assert len(citas_de(estado_fresco, "E1")) == 1


def test_no_se_reemplaza_nada_sin_un_aviso_previo_de_la_herramienta(montar, estado_fresco):
    acciones = [("proponer_opciones", CARRERA), ("reservar_cita", {"numero": 1, "reemplazar": True})]
    cliente, _ = montar(guion_r7(acciones))
    sid = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()["session_id"]
    r = cliente.post("/api/chat", json={"mensaje": "sí, cámbiala", "estudiante_id": "E1", "session_id": sid}).json()
    assert r["cita"] is None and "Solo se reemplaza una cita después de que" in r["respuesta"]
    assert citas_de(estado_fresco, "E1") == []


# --- opciones: máximo 3, servicio por nombre, desencuentro solo sin cupos -------------------------------------------


def test_el_chat_nunca_muestra_mas_de_3_opciones(montar):
    cliente, _ = montar(guion_r7([("proponer_opciones", {**CARRERA, "k": 5})]))
    r = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()
    assert 1 <= len(r["opciones"]) <= 3


def test_el_agente_pasa_el_servicio_que_la_persona_nombro(montar):
    cliente, _ = montar(guion_r7([("proponer_opciones", {**CARRERA, "service_id_preferido": "Espacio Lumen Trayectoria"})]))
    r = cliente.post("/api/chat", json={"mensaje": "quiero Lumen Trayectoria el miércoles por videollamada", "estudiante_id": "E1"}).json()
    assert r["opciones"] and {o["service_id"] for o in r["opciones"]} == {"SRV_AE_006"}


def test_no_se_registra_un_desencuentro_si_hay_cupos_compatibles(montar, estado_fresco):
    acciones = [("proponer_opciones", CARRERA), ("registrar_desencuentro", {})]
    cliente, _ = montar(guion_r7(acciones))
    sid = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()["session_id"]
    antes = len(estado_fresco.desencuentros)
    r = cliente.post(
        "/api/chat", json={"mensaje": "no me sirve ninguna", "estudiante_id": "E1", "session_id": sid}
    ).json()
    assert r["desencuentro_registrado"] is False and len(estado_fresco.desencuentros) == antes
    assert "no es un desencuentro" in r["respuesta"]


def test_sin_cupos_el_mensaje_viene_del_backend_y_el_desencuentro_se_registra(montar, estado_fresco):
    sin_cupos = {**CARRERA, "franjas": [{"dia": "Wed", "desde": "19:00", "hasta": "21:00"}], "grupo": "nocturno"}
    vistos = []

    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        if r is None:
            return llamada("proponer_opciones", **sin_cupos)
        vistos.append(r)
        if r.get("motivo_vacio"):
            return llamada("registrar_desencuentro")
        return AIMessage("Avisé al equipo.")

    cliente, _ = montar(guion)
    r = cliente.post(
        "/api/chat", json={"mensaje": "Trabajo de día, solo puedo el miércoles de 19 a 21 por videollamada", "estudiante_id": "E_NOCHE"}
    ).json()
    assert r["opciones"] == [] and r["desencuentro_registrado"] is True
    assert vistos[0]["mensaje"].startswith("No encontré cupos dentro de los días, horarios y canales que puedes.")
    assert vistos[0]["desencuentro_registrado"] is True and "No le propongas otros días, horas ni canales" in vistos[0]["indicacion"]
    [fila] = [d for d in estado_fresco.desencuentros if d["estudiante_id"] == "E_NOCHE"]
    assert fila["grupo"] == "nocturno" and fila["franjas"][0]["desde"] == "19:00"
    assert json.dumps(vistos[0]).count("18:00") == 0  # no se sugiere ningún horario fuera de lo que la persona dijo


def test_sin_cupos_la_herramienta_registra_el_desencuentro_aunque_el_modelo_no_lo_pida(montar, estado_fresco):
    """La regla vive en la herramienta: un modelo pequeño que se salta `registrar_desencuentro` no la rompe."""
    sin_cupos = {**CARRERA, "franjas": [{"dia": "Wed", "desde": "19:00", "hasta": "21:00"}]}

    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        return llamada("proponer_opciones", **sin_cupos) if r is None else AIMessage("¿Quieres que te avise si se libera un cupo?")

    cliente, _ = montar(guion)
    r = cliente.post(
        "/api/chat", json={"mensaje": "solo puedo el miércoles de 19 a 21, por videollamada", "estudiante_id": "E_NOCHE"}
    ).json()
    assert r["desencuentro_registrado"] is True and r["opciones"] == []
    assert [d["estudiante_id"] for d in estado_fresco.desencuentros if d["estudiante_id"] == "E_NOCHE"] == ["E_NOCHE"]
    [evento] = [e for e in cliente.get("/api/coordinacion/actividad").json()["eventos"] if e["tipo"] == "desencuentro"]
    assert evento["origen"] == "chat" and evento["estudiante_id"] == "E_NOCHE"


def test_con_cupos_compatibles_no_se_registra_ningun_desencuentro(montar, estado_fresco):
    cliente, _ = montar(guion_r7([("proponer_opciones", CARRERA)]))
    antes = len(estado_fresco.desencuentros)
    r = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()
    assert r["opciones"] and r["desencuentro_registrado"] is False and len(estado_fresco.desencuentros) == antes


def test_un_solo_desencuentro_por_servicio_ideal_y_franja_dentro_de_la_conversacion(montar, estado_fresco):
    noche = {**CARRERA, "franjas": [{"dia": "Wed", "desde": "19:00", "hasta": "21:00"}]}
    otra_franja = {**CARRERA, "franjas": [{"dia": "Thu", "desde": "19:00", "hasta": "21:00"}]}

    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        humanos = [m for m in mensajes if m.type == "human"]
        if r is not None:
            return AIMessage("ok")
        if len(humanos) == 3:
            return llamada("proponer_opciones", **otra_franja)
        return llamada("proponer_opciones", **noche)

    cliente, _ = montar(guion)
    sid = None
    for texto in ("solo puedo el miércoles de 19 a 21 por videollamada", "sí, el miércoles de 19 a 21 por videollamada", "mejor el jueves de 19 a 21 por videollamada"):
        r = cliente.post("/api/chat", json={"mensaje": texto, "estudiante_id": "E_DOBLE", "session_id": sid}).json()
        sid = r["session_id"]
    filas = [d for d in estado_fresco.desencuentros if d["estudiante_id"] == "E_DOBLE"]
    # el mismo servicio ideal y franja se registró una vez; otra franja es otro desencuentro
    assert sorted(f["franjas"][0]["dia_semana"] for f in filas) == [2, 3] and len(filas) == 2
    # y el modelo que además llama a registrar_desencuentro tampoco lo duplica
    cliente2, _ = montar(guion_r7([("proponer_opciones", noche), ("registrar_desencuentro", {})]))
    s2 = cliente2.post("/api/chat", json={"mensaje": "solo puedo el miércoles de 19 a 21 por videollamada", "estudiante_id": "E_TRIPLE"}).json()["session_id"]
    cliente2.post("/api/chat", json={"mensaje": "no me sirve", "estudiante_id": "E_TRIPLE", "session_id": s2})
    assert len([d for d in estado_fresco.desencuentros if d["estudiante_id"] == "E_TRIPLE"]) == 1
