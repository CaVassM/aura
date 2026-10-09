"""Agente + herramientas + API de chat, con un modelo guionado en lugar de Ollama."""

import json
import uuid

import pytest

pytest.importorskip("langchain")
pytest.importorskip("langchain_ollama")

from fastapi.testclient import TestClient
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from agente.agente import AgenteAura
from app.main import create_app

# La demo sembrada (escenario de estrés) casi no tiene cupos digitales lunes y martes; miércoles sí.
PARAMS_PROPONER = {
    "motivo": "academic_pressure",
    "franjas": [{"dia": "Wed", "desde": "09:00", "hasta": "18:00"}],
    "canales_aceptables": ["digital"],
    "distrito": "DIST_GAIA",
}


# Mensaje con lo mínimo que exige el agente para buscar: días y canal dichos por la persona.
MSG = "Tengo parciales, puedo el miércoles por videollamada"


def llamada(nombre: str, **args) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": nombre, "args": args, "id": uuid.uuid4().hex}])


class ModeloGuionado(BaseChatModel):
    """Decide su respuesta con una función de los mensajes; no usa red ni Ollama."""

    guion: object
    llamadas: int = 0

    @property
    def _llm_type(self) -> str:
        return "guionado"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.llamadas += 1
        return ChatResult(generations=[ChatGeneration(message=self.guion(messages))])


def citas_de(estado, estudiante_id):
    """La demo ya viene sembrada con cientos de citas: se mira solo la de quien prueba."""
    return [c for c in estado.motor.citas() if c["estudiante_id"] == estudiante_id]


def ultimo_resultado(mensajes) -> dict | None:
    """JSON de la última herramienta ejecutada, si el turno actual ya llamó a una."""
    if isinstance(mensajes[-1], ToolMessage):
        return json.loads(mensajes[-1].content)
    return None


@pytest.fixture()
def montar(settings, estado_fresco):
    def _montar(guion):
        modelo = ModeloGuionado(guion=guion)
        cliente = TestClient(create_app(settings, estado_fresco, agente=AgenteAura(modelo=modelo)))
        cliente.__enter__()
        return cliente, modelo

    clientes = []

    def fabrica(guion):
        cliente, modelo = _montar(guion)
        clientes.append(cliente)
        return cliente, modelo

    yield fabrica
    for c in clientes:
        c.__exit__(None, None, None)


def proponer_y_responder(mensajes):
    r = ultimo_resultado(mensajes)
    if r is None:
        return llamada("proponer_opciones", **PARAMS_PROPONER)
    return AIMessage(f"Encontré {len(r['opciones'])} opciones.")


def test_proponer_devuelve_tarjetas_sin_reservar(montar, estado_fresco):
    cliente, _ = montar(proponer_y_responder)
    r = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["session_id"] and cuerpo["respuesta"].startswith("Encontré")
    assert cuerpo["opciones"] and cuerpo["cita"] is None
    assert [h["nombre"] for h in cuerpo["herramientas_usadas"]] == ["proponer_opciones"]
    assert citas_de(estado_fresco, "E1") == []  # proponer no retiene nada


def test_reservar_en_el_segundo_mensaje_crea_la_cita_para_la_persona(montar, estado_fresco):
    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        if r is None:
            humanos = [m for m in mensajes if m.type == "human"]
            if len(humanos) == 1:
                return llamada("proponer_opciones", **PARAMS_PROPONER)
            return llamada("reservar_cita", numero=1)  # «la primera»
        if "cita" in r:
            return AIMessage(f"Listo, cita {r['cita']['cita_id']}.")
        return AIMessage("Estas son las opciones.")

    cliente, _ = montar(guion)
    primero = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()
    segundo = cliente.post(
        "/api/chat", json={"mensaje": "La primera", "estudiante_id": "E1", "session_id": primero["session_id"]}
    ).json()
    assert segundo["cita"]["estudiante_id"] == "E1" and segundo["cita"]["estado"] == "confirmada"
    assert segundo["opciones"] == []
    # La cita es la misma que ve «Mis citas» y Coordinación.
    mias = cliente.get("/api/appointments", params={"estudiante_id": "E1"}).json()
    assert [c["id"] for c in mias] == [segundo["cita"]["id"]]
    assert len(citas_de(estado_fresco, "E1")) == 1


def test_no_reserva_opciones_inexistentes(montar, estado_fresco):
    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        if r is None:
            return llamada("proponer_opciones", **PARAMS_PROPONER)
        if "opciones" in r:
            return llamada("reservar_cita", numero=9)
        return AIMessage(f"No pude: {r['error']}")

    cliente, _ = montar(guion)
    r = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()
    assert r["cita"] is None and r["respuesta"] == "No pude: opcion_no_propuesta"
    assert citas_de(estado_fresco, "E1") == []


def test_el_modelo_no_puede_cancelar_citas_de_otra_persona(montar, estado_fresco):
    opcion = estado_fresco.motor.proponer_opciones(
        {**PARAMS_PROPONER, "estudiante_id": "DUENA", "grupo": "diurno"}, 1
    )["opciones"][0]["opcion_id"]
    ajena = estado_fresco.motor.reservar("DUENA", opcion)["cita"]["cita_id"]

    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        return llamada("cancelar_cita", cita_id=ajena) if r is None else AIMessage(r.get("error", "cancelada"))

    cliente, _ = montar(guion)
    r = cliente.post("/api/chat", json={"mensaje": "cancela la cita CITA-0000001", "estudiante_id": "OTRA"}).json()
    assert r["respuesta"] == "cita_no_encontrada" and r["cita_cancelada"] is None
    assert len(citas_de(estado_fresco, "DUENA")) == 1


def test_cancelar_propia_libera_el_cupo(montar, estado_fresco):
    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        humanos = len([m for m in mensajes if m.type == "human"])
        if r is None and humanos == 1:
            return llamada("proponer_opciones", **PARAMS_PROPONER)
        if r is None and humanos == 2:
            return llamada("reservar_cita", numero=1)
        if r is None:
            ultima = [m for m in mensajes if isinstance(m, ToolMessage)][-1]
            return llamada("cancelar_cita", cita_id=json.loads(ultima.content)["cita"]["cita_id"])
        return AIMessage("ok")

    cliente, _ = montar(guion)
    sid = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()["session_id"]
    cliente.post("/api/chat", json={"mensaje": "la primera", "estudiante_id": "E1", "session_id": sid})
    r = cliente.post("/api/chat", json={"mensaje": "mejor cancélala", "estudiante_id": "E1", "session_id": sid}).json()
    assert r["cita_cancelada"]["estado"] == "cancelada"
    assert citas_de(estado_fresco, "E1") == []


def test_desencuentro_usa_la_ultima_busqueda_sin_que_el_modelo_la_repita(montar, estado_fresco):
    sin_cupos = {**PARAMS_PROPONER, "franjas": [{"dia": "Sun", "desde": "03:00", "hasta": "04:00"}]}

    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        if r is None:
            return llamada("proponer_opciones", **sin_cupos)
        if r.get("motivo_vacio"):
            return llamada("registrar_desencuentro")
        return AIMessage("Avisé al equipo.")

    cliente, _ = montar(guion)
    r = cliente.post("/api/chat", json={"mensaje": "solo puedo el domingo de madrugada, por teléfono", "estudiante_id": "E1"}).json()
    assert r["desencuentro_registrado"] and r["opciones"] == []
    [fila] = [d for d in estado_fresco.desencuentros if d["estudiante_id"] == "E1"]
    assert fila["motivo"] == "academic_pressure"


def test_crisis_responde_con_ayuda_sin_llamar_al_modelo(montar):
    cliente, modelo = montar(lambda m: AIMessage("no debería llamarse"))
    r = cliente.post("/api/chat", json={"mensaje": "A veces pienso en quitarme la vida", "estudiante_id": "E1"}).json()
    assert r["alerta_crisis"] and "113" in r["respuesta"]
    assert modelo.llamadas == 0 and r["opciones"] == []


def test_falta_distrito_si_no_se_conoce(montar):
    sin_distrito = {k: v for k, v in PARAMS_PROPONER.items() if k != "distrito"}

    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        return llamada("proponer_opciones", **sin_distrito) if r is None else AIMessage(r.get("error", "ok"))

    cliente, _ = montar(guion)
    assert cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()["respuesta"] == "falta_distrito"
    con_contexto = cliente.post(
        "/api/chat", json={"mensaje": MSG, "estudiante_id": "E1", "distrito": "dist_gaia"}
    ).json()
    assert con_contexto["respuesta"] == "ok" and con_contexto["opciones"]


def test_sesiones_son_de_su_dueno_y_se_pueden_leer_y_borrar(montar):
    cliente, _ = montar(proponer_y_responder)
    sid = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()["session_id"]
    ajeno = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E2", "session_id": sid})
    assert ajeno.status_code == 404
    historial = cliente.get(f"/api/chat/{sid}", params={"estudiante_id": "E1"}).json()
    assert [m["rol"] for m in historial["mensajes"]] == ["user", "agent"]
    assert cliente.delete(f"/api/chat/{sid}", params={"estudiante_id": "E1"}).json() == {"ok": True}
    assert cliente.get(f"/api/chat/{sid}", params={"estudiante_id": "E1"}).status_code == 404


def test_validaciones_de_entrada(montar):
    cliente, _ = montar(proponer_y_responder)
    assert cliente.post("/api/chat", json={"mensaje": "", "estudiante_id": "E1"}).status_code == 422
    assert cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1", "distrito": "X"}).status_code == 422
    assert cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1", "grupo": "tarde"}).status_code == 422


def test_modelo_sin_respuesta_usa_texto_de_respaldo(montar):
    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        if r is None:
            return llamada("proponer_opciones", **PARAMS_PROPONER)
        return AIMessage("")

    cliente, _ = montar(guion)
    r = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"}).json()
    assert r["respuesta"]  # nunca llega vacío a la burbuja


def test_ollama_apagado_es_503_con_instrucciones(settings, estado_fresco):
    import httpx

    class Roto(ModeloGuionado):
        def _generate(self, *a, **k):
            raise httpx.ConnectError("refused")

    agente = AgenteAura(modelo=Roto(guion=None))
    with TestClient(create_app(settings, estado_fresco, agente=agente)) as cliente:
        r = cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"})
    assert r.status_code == 503 and r.json()["error"] == "agente_no_disponible"
    assert "ollama serve" in r.json()["detalle"]


def test_estado_del_agente_responde_sin_ollama(montar, monkeypatch):
    monkeypatch.setenv("AURA_OLLAMA_URL", "http://127.0.0.1:9")  # puerto cerrado
    cliente, _ = montar(proponer_y_responder)
    r = cliente.get("/api/chat/estado")
    assert r.status_code == 200
    assert r.json()["ollama_disponible"] is False and r.json()["modelo"] == "gemma4"


def test_no_busca_si_la_persona_no_dijo_dias_ni_canal(montar, estado_fresco):
    """«¿qué servicios existen?» no debe disparar una búsqueda con días y canal inventados por el modelo."""
    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        return llamada("proponer_opciones", **PARAMS_PROPONER) if r is None else AIMessage(r.get("error", "buscó"))

    cliente, _ = montar(guion)
    r = cliente.post("/api/chat", json={"mensaje": "¿Qué servicios existen?", "estudiante_id": "E1"}).json()
    assert r["respuesta"] == "faltan_datos" and r["opciones"] == []
    solo_dias = cliente.post(
        "/api/chat", json={"mensaje": "puedo el lunes", "estudiante_id": "E1", "session_id": r["session_id"]}
    ).json()
    assert solo_dias["respuesta"] == "faltan_datos"  # sigue faltando el canal
    completo = cliente.post(
        "/api/chat", json={"mensaje": "da igual el canal", "estudiante_id": "E1", "session_id": r["session_id"]}
    ).json()
    assert completo["respuesta"] == "buscó" and completo["opciones"]  # los días del mensaje anterior cuentan


def test_el_modelo_no_ve_identificadores_internos(montar):
    vistos = []

    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        if r is None:
            return llamada("proponer_opciones", **PARAMS_PROPONER)
        vistos.append(json.dumps(r, ensure_ascii=False))
        return AIMessage("ok")

    cliente, _ = montar(guion)
    cliente.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E1"})
    assert vistos and "|" not in vistos[0] and '"C0' not in vistos[0] and "SRV_" not in vistos[0]
    opcion = json.loads(vistos[0])["opciones"][0]
    assert opcion["numero"] == 1 and "miércoles" in opcion["texto"] and "noviembre" in opcion["texto"]
