"""Lista de espera: anotarse sin cupo y recibir aviso cuando se libera uno."""

import pytest

pytest.importorskip("langchain")

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage

from agente.agente import AgenteAura
from agente.entrada import acepta_aviso
from app.main import create_app
from tests.test_agente_chat import ModeloGuionado, PARAMS_PROPONER, MSG, llamada, ultimo_resultado

SOLICITUD = {
    "motivo": "academic_pressure",
    "distrito": "DIST_NEBULA",
    "franjas": [{"dia": "Wed", "desde": "09:00", "hasta": "21:00"}],
    "canales_aceptables": ["digital"],
    "fecha": "2026-11-18",
}


def test_anotarse_y_aviso_al_liberarse_un_cupo(client_fresco):
    c = client_fresco
    # Se agota todo lo que sirve en un miércoles concreto y la persona se anota
    ocupadas = []
    for i in range(80):
        r = c.post("/api/appointments/proposals?k=20", json={"estudiante_id": f"X{i}", **{k: v for k, v in SOLICITUD.items() if k != "fecha"}}).json()
        if not r["opciones"]:
            break
        ocupadas.append(c.post("/api/appointments", json={"estudiante_id": f"X{i}", "opcion_id": r["opciones"][0]["opcion_id"]}).json())
    assert ocupadas
    sin = c.post("/api/appointments/proposals?k=3", json={"estudiante_id": "E_ESP", **{k: v for k, v in SOLICITUD.items() if k != "fecha"}}).json()
    assert sin["opciones"] == []

    espera = c.post("/api/appointments/lista-espera", json={"estudiante_id": "E_ESP", **{k: v for k, v in SOLICITUD.items() if k != "fecha"}})
    assert espera.status_code == 201 and espera.json()["estado"] == "esperando"
    # repetirlo no duplica
    otra = c.post("/api/appointments/lista-espera", json={"estudiante_id": "E_ESP", **{k: v for k, v in SOLICITUD.items() if k != "fecha"}})
    assert otra.json()["id"] == espera.json()["id"]
    assert len(c.get("/api/estudiantes/E_ESP/lista-espera").json()["esperas"]) == 1

    # Alguien cancela: a E_ESP le llega el aviso con la opción
    c.delete(f"/api/appointments/{ocupadas[0]['id']}", params={"estudiante_id": ocupadas[0]["estudiante_id"]})
    avisos = c.get("/api/estudiantes/E_ESP/avisos").json()["avisos"]
    assert [a["tipo"] for a in avisos] == ["cupo_disponible"]
    assert avisos[0]["opciones"] and "Se liberó un cupo" in avisos[0]["mensaje"]
    mia = c.get("/api/estudiantes/E_ESP/lista-espera").json()["esperas"][0]
    assert mia["estado"] == "avisada" and mia["opcion"]["opcion_id"] == avisos[0]["opciones"][0]["opcion_id"]
    # y la opción se puede reservar
    reserva = c.post("/api/appointments", json={"estudiante_id": "E_ESP", "opcion_id": mia["opcion"]["opcion_id"]})
    assert reserva.status_code == 201
    # Coordinación lo ve
    tipos = [e["tipo"] for e in c.get("/api/coordinacion/actividad").json()["eventos"]]
    assert "lista_espera_alta" in tipos and "lista_espera_aviso" in tipos


def test_un_mismo_cupo_no_se_avisa_a_dos_personas(client_fresco):
    """Al cancelar, el servicio sale del modo lote y se liberan varios cupos: cada persona recibe uno distinto."""
    c = client_fresco
    solicitud = {k: v for k, v in SOLICITUD.items() if k != "fecha"}
    ocupadas = []
    for i in range(80):
        r = c.post("/api/appointments/proposals?k=20", json={"estudiante_id": f"X{i}", **solicitud}).json()
        if not r["opciones"]:
            break
        ocupadas.append(c.post("/api/appointments", json={"estudiante_id": f"X{i}", "opcion_id": r["opciones"][0]["opcion_id"]}).json())
    for e in ("A", "B"):
        c.post("/api/appointments/lista-espera", json={"estudiante_id": e, **solicitud})
    c.delete(f"/api/appointments/{ocupadas[0]['id']}", params={"estudiante_id": ocupadas[0]["estudiante_id"]})
    a = c.get("/api/estudiantes/A/avisos").json()["avisos"]
    b = c.get("/api/estudiantes/B/avisos").json()["avisos"]
    assert len(a) == 1 and len(b) == 1
    cupo = lambda aviso: aviso["opciones"][0]["opcion_id"].split("|")[0]
    assert cupo(a[0]) != cupo(b[0])


def test_salir_de_la_lista_y_no_ajena(client_fresco):
    c = client_fresco
    solicitud = {k: v for k, v in SOLICITUD.items() if k != "fecha"}
    espera = c.post("/api/appointments/lista-espera", json={"estudiante_id": "A", **solicitud}).json()
    assert c.delete(f"/api/estudiantes/B/lista-espera/{espera['id']}").status_code == 404
    assert c.delete(f"/api/estudiantes/A/lista-espera/{espera['id']}").json()["estado"] == "cancelada"
    mala = c.post("/api/appointments/lista-espera", json={"estudiante_id": "A", **{**solicitud, "motivo": "inventado"}})
    assert mala.status_code == 422


@pytest.mark.parametrize("mensaje,ultima,esperado", [
    ("sí, avísame si se libera algo", "", True),
    ("avísame cuando haya un cupo", "", True),
    ("sí", "¿Quieres que te avise aquí si se libera un cupo?", True),
    ("sí", "¿Te gustaría ampliar los días?", False),
    ("no gracias", "¿Quieres que te avise si se libera un cupo?", False),
    ("mmm no sé", "¿Quieres que te avise si se libera un cupo?", False),
])
def test_acepta_aviso(mensaje, ultima, esperado):
    assert acepta_aviso(mensaje, ultima) is esperado


def test_el_agente_anota_en_lista_de_espera_solo_si_la_persona_acepta(settings, estado_fresco):
    def guion(mensajes):
        r = ultimo_resultado(mensajes)
        humanos = [m.content for m in mensajes if m.type == "human"]
        if r is None:
            if len(humanos) == 1:
                return llamada("proponer_opciones", **{**PARAMS_PROPONER, "fecha": "2026-11-22"})  # domingo: sin cupos
            return llamada("avisarme_si_hay_cupo")
        if r.get("error") == "falta_confirmacion":
            return AIMessage("falta_confirmacion")
        if r.get("ok") and "indicacion" in r:
            return AIMessage("Listo, te aviso aquí.")
        return AIMessage("¿Quieres que te avise aquí si se libera un cupo?")

    modelo = ModeloGuionado(guion=guion)
    with TestClient(create_app(settings, estado_fresco, agente=AgenteAura(modelo=modelo))) as c:
        primero = c.post("/api/chat", json={"mensaje": MSG, "estudiante_id": "E_ESP"}).json()
        sid = primero["session_id"]
        duda = c.post("/api/chat", json={"mensaje": "mmm déjame pensarlo", "estudiante_id": "E_ESP", "session_id": sid}).json()
        assert duda["respuesta"] == "falta_confirmacion" and duda["lista_espera"] is None
        assert c.get("/api/estudiantes/E_ESP/lista-espera").json()["esperas"] == []
        si = c.post("/api/chat", json={"mensaje": "sí, avísame si se libera un cupo", "estudiante_id": "E_ESP", "session_id": sid}).json()
        assert si["lista_espera"]["id"].startswith("ESP-")
        assert len(c.get("/api/estudiantes/E_ESP/lista-espera").json()["esperas"]) == 1
