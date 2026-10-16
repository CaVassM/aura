"""Modo lote: servicios con utilización ≥ umbral se reparten en conjunto, el lote se cierra solo y avisa."""

import time

import pytest

from app.services.citas_service import CitasService
from app.services.lote_service import LoteService
from app.services.ocupacion import embudo_por_servicio

SOLICITUD = {
    "motivo": "academic_pressure",
    "distrito": "DIST_GAIA",
    "grupo": "diurno",
    "franjas": [{"dia": d, "desde": "09:00", "hasta": "18:00"} for d in ("Mon", "Tue", "Wed", "Thu", "Fri")],
    "canales_aceptables": ["digital"],
}


def de(estudiante, **cambios):
    return {**SOLICITUD, "estudiante_id": estudiante, **cambios}


def esperar(condicion, segundos=8):
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        if condicion():
            return True
        time.sleep(0.1)
    return False


@pytest.fixture()
def todo_en_lote(estado_fresco):
    """Umbral 0: todos los servicios con cupos liberados están en modo lote."""
    estado_fresco.parametros["modo_lote_umbral_utilizacion"] = 0.0
    estado_fresco.parametros["lote"].update({"ventana_segundos": 60, "tamano_maximo": 2})
    return estado_fresco


def lotes(client):
    return client.get("/api/coordinacion/lotes").json()


def eventos(client, tipo=None):
    todos = client.get("/api/coordinacion/actividad").json()["eventos"]
    return [e for e in todos if tipo is None or e["tipo"] == tipo]


def test_el_umbral_es_75_y_sale_de_un_solo_valor_del_yaml(estado_fresco, client_fresco):
    assert estado_fresco.parametros["modo_lote_umbral_utilizacion"] == 0.75
    assert lotes(client_fresco)["umbral_pct"] == 75.0
    # el nivel «alta» del panel es el mismo corte: no hay un segundo valor
    assert "alta_mayor_que" not in estado_fresco.parametros["coordinacion"]["nivel_ocupacion"]
    assert client_fresco.get("/api/demo/estado").json()["umbrales_nivel"]["alta_desde"] == 75.0
    assert client_fresco.get("/api/coordinacion/reglas").json()["modo_lote"]["umbral_pct"] == 75.0


def test_alta_y_en_lote_son_lo_mismo(estado_fresco, client_fresco):
    panorama = lotes(client_fresco)
    assert any(s["en_lote"] for s in panorama["servicios"])
    assert all((s["pct"] >= 75) == s["en_lote"] for s in panorama["servicios"])
    for s in client_fresco.get("/api/coordinacion/resumen").json()["servicios"]:
        assert (s["nivel"] == "alta") == (s["ocupacion_pct"] >= 75)


def test_un_servicio_en_lote_no_se_oculta_sale_como_una_sola_opcion_de_tipo_lote(client_fresco, estado_fresco):
    panorama = lotes(client_fresco)
    en_lote = {s["service_id"] for s in panorama["servicios"] if s["en_lote"]}
    assert en_lote
    # peer_support (motivo social_support): hay servicios sobre y bajo el umbral
    pedido = de("E1", motivo="social_support", canales_aceptables=["digital", "phone", "in_person"])
    propuesta = client_fresco.post("/api/appointments/proposals?k=20", json=pedido).json()
    opciones = propuesta["opciones"]
    assert 1 <= len(opciones) <= 3  # máximo 3, aunque se pida más
    for o in opciones:
        assert (o["tipo_opcion"] == "lote") == (o["service_id"] in en_lote)  # cada servicio en lote: opción de lote
        if o["tipo_opcion"] == "lote":
            assert o["opcion_id"] == f"LOTE|{o['service_id']}" and o["fecha"] is None and o["cupos_libres"] > 0
            assert o["tiempo_respuesta_s"] == 30 and "mucha demanda" in o["mensaje"]
    assert len({o["service_id"] for o in opciones if o["tipo_opcion"] == "lote"}) == len([o for o in opciones if o["tipo_opcion"] == "lote"])


def test_si_todo_esta_en_lote_hay_opciones_de_lote_no_un_vacio(client_fresco, todo_en_lote):
    r = client_fresco.post("/api/appointments/proposals", json=de("E1")).json()
    assert r["opciones"] and all(o["tipo_opcion"] == "lote" for o in r["opciones"]) and r["motivo_vacio"] is None
    assert r["mensaje"] == "Este servicio tiene mucha demanda; sus cupos se reparten en grupo. Te confirmo en unos segundos."
    assert r["opciones"][0]["tiempo_respuesta_s"] == 60  # la ventana del lote


def test_entrar_al_lote_abre_la_cuenta_regresiva_y_se_ve_en_coordinacion(client_fresco, todo_en_lote):
    r = client_fresco.post("/api/appointments/lote", json=de("E1"))
    assert r.status_code == 201
    estado = r.json()["lote"]
    assert estado["estado"] == "en_espera" and estado["posicion"] == 1 and estado["solicitudes"] == 1
    abierto = lotes(client_fresco)["abierto"]
    assert abierto["id"] == estado["id"] and abierto["estado"] == "abierto"
    assert [s["estudiante_id"] for s in abierto["solicitudes"]] == ["E1"]
    assert abierto["solicitudes"][0]["motivo_label"] == "Presión académica"
    assert [e["tipo"] for e in eventos(client_fresco)] == ["lote_abierto"]
    avisos = client_fresco.get("/api/estudiantes/E1/avisos").json()["avisos"]
    assert [a["tipo"] for a in avisos] == ["lote_en_espera"]


def test_no_se_puede_estar_dos_veces_en_el_mismo_lote(client_fresco, todo_en_lote):
    assert client_fresco.post("/api/appointments/lote", json=de("E1")).status_code == 201
    r = client_fresco.post("/api/appointments/lote", json=de("E1"))
    assert r.status_code == 409 and r.json()["error"] == "ya_en_lote"


def test_el_lote_solo_vale_si_hay_un_servicio_compatible_en_modo_lote(client_fresco, estado_fresco):
    estado_fresco.parametros["modo_lote_umbral_utilizacion"] = 1e6  # ninguno en lote
    r = client_fresco.post("/api/appointments/lote", json=de("E1"))
    assert r.status_code == 422 and "modo lote" in r.json()["detalle"]


def test_el_lote_se_cierra_solo_al_juntar_el_maximo_y_asigna_en_conjunto(client_fresco, todo_en_lote):
    client_fresco.post("/api/appointments/lote", json=de("E1"))
    client_fresco.post("/api/appointments/lote", json=de("E2", franjas=[{"dia": "Wed", "desde": "09:00", "hasta": "18:00"}]))
    assert esperar(lambda: lotes(client_fresco)["historial"]), "el lote debía cerrarse solo"
    panorama = lotes(client_fresco)
    assert panorama["abierto"] is None
    [lote] = panorama["historial"]
    r = lote["resultado"]
    assert lote["estado"] == "resuelto" and r["asignados"] == 2 and r["sin_cupo"] == 0
    assert r["genetico"]["asignados"] == 2 and r["llegada"]["asignados"] == 2 and r["tiempo_s"] >= 0
    assert {a["estudiante_id"] for a in r["asignaciones"]} == {"E1", "E2"}
    assert sorted(a["orden_asignacion"] for a in r["asignaciones"]) == [1, 2]
    # Las citas quedan reservadas a nombre de cada persona
    for est in ("E1", "E2"):
        [cita] = client_fresco.get("/api/appointments", params={"estudiante_id": est}).json()
        assert cita["estado"] == "confirmada"
    tipos = [(e["tipo"], e["origen"]) for e in eventos(client_fresco)]
    assert tipos.count(("cita_reservada", "lote")) == 2 and ("lote_resuelto", "lote") in tipos
    # cada persona recibe su aviso en vivo, con la cita
    for est in ("E1", "E2"):
        avisos = client_fresco.get(f"/api/estudiantes/{est}/avisos").json()["avisos"]
        assert [a["tipo"] for a in avisos] == ["lote_en_espera", "lote_asignada"]
        assert avisos[1]["cita"]["estudiante_id"] == est and "Tu número de cita" in avisos[1]["mensaje"]


def test_el_lote_se_cierra_solo_por_tiempo(client_fresco, todo_en_lote):
    todo_en_lote.parametros["lote"]["ventana_segundos"] = 1
    client_fresco.post("/api/appointments/lote", json=de("E1"))
    assert lotes(client_fresco)["abierto"] is not None
    assert esperar(lambda: lotes(client_fresco)["historial"], 6)
    assert lotes(client_fresco)["historial"][0]["resultado"]["asignados"] == 1


def test_entrar_a_un_lote_nunca_registra_desencuentro(client_fresco, estado_fresco, todo_en_lote):
    antes = len(estado_fresco.desencuentros)
    assert client_fresco.post("/api/appointments/lote", json=de("E1")).status_code == 201
    assert len(estado_fresco.desencuentros) == antes
    assert eventos(client_fresco, "desencuentro") == []


def test_quien_no_recibe_cupo_y_ya_no_hay_ninguno_compatible_queda_como_desencuentro(client_fresco, todo_en_lote):
    # Un solo cupo libre en toda la red: solo uno de los dos puede quedar, y al otro ya no le queda ninguna opción.
    agenda = todo_en_lote.motor._agenda
    libres = agenda.libres_ahora()  # la demo ya trae cientos de cupos reservados: hay que partir de uno realmente libre
    cupo = next(c for c in agenda.cupos if c.id in libres and c.fecha.weekday() == 2 and c.tipo == "counseling"
                and "digital" in c.canales and c.fecha > agenda.hoy)
    agenda.libres_base = {cupo.id}
    miercoles = [{"dia": "Wed", "desde": "09:00", "hasta": "18:00"}]
    client_fresco.post("/api/appointments/lote", json=de("E1", franjas=miercoles))
    client_fresco.post("/api/appointments/lote", json=de("E2", franjas=miercoles))
    assert esperar(lambda: lotes(client_fresco)["historial"])
    r = lotes(client_fresco)["historial"][0]["resultado"]
    assert r["asignados"] == 1 and r["sin_cupo"] == 1 and len(r["sin_cupo_estudiantes"]) == 1
    perdedor = r["sin_cupo_estudiantes"][0]
    avisos = client_fresco.get(f"/api/estudiantes/{perdedor}/avisos").json()["avisos"]
    assert avisos[-1]["tipo"] == "lote_sin_cupo" and "lista de espera" in avisos[-1]["mensaje"]
    assert [e["origen"] for e in eventos(client_fresco, "desencuentro")] == ["lote"]


def test_quien_no_recibe_cupo_pero_aun_hay_opciones_las_recibe_y_no_es_desencuentro(client_fresco, estado_fresco, todo_en_lote):
    # Dos personas quieren consejería (solo ese servicio) y hay un único cupo de consejería: una se queda sin él.
    # Como todavía existe un cupo compatible (de apoyo entre pares), NO es un desencuentro: se le ofrece.
    agenda = todo_en_lote.motor._agenda
    libres = agenda.libres_ahora()
    consejeria = next(c for c in agenda.cupos if c.id in libres and c.fecha.weekday() == 2 and c.tipo == "counseling"
                      and "digital" in c.canales and c.fecha > agenda.hoy)
    pares = next(c for c in agenda.cupos if c.id in libres and c.fecha.weekday() == 2 and c.tipo == "peer_support"
                 and "phone" in c.canales and c.fecha > agenda.hoy)
    agenda.libres_base = {consejeria.id, pares.id}
    antes = len(estado_fresco.desencuentros)
    miercoles = [{"dia": "Wed", "desde": "09:00", "hasta": "18:00"}]
    for est in ("E1", "E2"):
        r = client_fresco.post(
            "/api/appointments/lote",
            json=de(est, franjas=miercoles, canales_aceptables=["digital", "phone"], solo_servicio_ideal=True),
        )
        assert r.status_code == 201, r.text
    assert esperar(lambda: lotes(client_fresco)["historial"])
    r = lotes(client_fresco)["historial"][0]["resultado"]
    assert r["asignados"] == 1 and r["sin_cupo"] == 1
    perdedor = r["sin_cupo_estudiantes"][0]
    assert len(estado_fresco.desencuentros) == antes and eventos(client_fresco, "desencuentro") == []
    aviso = client_fresco.get(f"/api/estudiantes/{perdedor}/avisos").json()["avisos"][-1]
    assert aviso["tipo"] == "lote_sin_cupo" and "1)" in aviso["mensaje"] and aviso["opciones"]
    assert aviso["opciones"][0]["tipo"] == "peer_support"


def test_reiniciar_la_demo_descarta_el_lote_abierto(client_fresco, todo_en_lote):
    todo_en_lote.parametros["lote"]["ventana_segundos"] = 1
    client_fresco.post("/api/appointments/lote", json=de("E1"))
    assert client_fresco.post("/api/demo/reiniciar").status_code == 200
    time.sleep(2.5)  # el temporizador del lote viejo ya venció: no debe hacer nada
    assert lotes(client_fresco)["abierto"] is None and lotes(client_fresco)["historial"] == []
    assert client_fresco.get("/api/appointments", params={"estudiante_id": "E1"}).json() == []


def test_cruzar_el_umbral_deja_un_evento_y_cancelar_lo_revierte(client_fresco, estado_fresco):
    agenda = estado_fresco.motor._agenda
    _, _, por = embudo_por_servicio(estado_fresco)
    # un servicio por debajo del umbral y un cupo libre suyo dentro de la ventana de reserva
    sid, fila = next((s, f) for s, f in sorted(por.items()) if f["reservados"] / f["liberados"] < 0.7)
    cupo = next(c for c in estado_fresco.motor.cupos_libres(sid)
                if (date_fromiso(c["fecha"]) - agenda.hoy).days <= agenda.ventana_dias)
    estado_fresco.parametros["modo_lote_umbral_utilizacion"] = (fila["reservados"] + 1) / fila["liberados"]
    citas = CitasService(estado_fresco)
    canal = cupo["canales"][0]
    cita = citas.reservar("E_UMBRAL", f"{cupo['cupo_id']}|{canal}")
    cruce = eventos(client_fresco, "servicio_en_lote")
    assert [e["servicio"]["service_id"] for e in cruce] == [sid] and cruce[0]["ocupacion"]["en_lote"] is True
    assert cruce[0]["umbral_pct"] > 0
    citas.cancelar(cita.id)
    assert len(eventos(client_fresco, "servicio_sale_de_lote")) == 1


def date_fromiso(texto):
    from datetime import date

    return date.fromisoformat(texto)


def test_entrar_exige_una_solicitud_valida(client_fresco, todo_en_lote):
    r = client_fresco.post("/api/appointments/lote", json=de("E1", motivo="inexistente"))
    assert r.status_code == 422


def test_el_servicio_expone_la_oferta_del_lote(estado_fresco):
    info = LoteService(estado_fresco).info_oferta()
    assert info == {"umbral_pct": 75.0, "ventana_s": 30, "tamano_maximo": 5, "abierto": False, "pendientes": 0, "cierra_en": None}


@pytest.fixture()
def consejeria_en_lote(estado_fresco, monkeypatch):
    """Solo los servicios de consejería en modo lote: lo directo son servicios alternativos (pares, vocacional)."""
    ids = {s["service_id"] for s in estado_fresco.motor.servicios() if s["tipo"] == "counseling"}
    monkeypatch.setattr(LoteService, "servicios_en_lote", lambda self: ids)
    estado_fresco.parametros["lote"].update({"ventana_segundos": 60, "tamano_maximo": 2})
    return ids


TODOS_LOS_CANALES = ["digital", "phone", "in_person"]


def test_el_servicio_ideal_en_lote_va_primero(client_fresco, consejeria_en_lote):
    pedido = de("E1", distrito="DIST_NEBULA", canales_aceptables=TODOS_LOS_CANALES)
    opciones = client_fresco.post("/api/appointments/proposals?k=5", json=pedido).json()["opciones"]
    assert len(opciones) == 3  # máximo 3
    assert all(o["tipo_opcion"] == "lote" and not o["es_alternativa"] for o in opciones)  # hay 5 consejerías: alcanzan


def test_quien_entra_al_lote_por_su_servicio_no_recibe_otro(client_fresco, estado_fresco, consejeria_en_lote):
    solicitud = de("E1", distrito="DIST_NEBULA", canales_aceptables=TODOS_LOS_CANALES)
    assert client_fresco.post("/api/appointments/lote", json=solicitud).status_code == 201
    client_fresco.post("/api/appointments/lote", json={**solicitud, "estudiante_id": "E2"})
    assert esperar(lambda: lotes(client_fresco)["historial"]), "el lote debía cerrarse solo"
    citas = [c for e in ("E1", "E2") for c in client_fresco.get("/api/appointments", params={"estudiante_id": e}).json()]
    assert citas and all(c["tipo"] == "counseling" for c in citas)  # solo consejería, nunca un alternativo


def test_un_servicio_en_lote_ya_no_exige_que_no_haya_opciones_directas(client_fresco, consejeria_en_lote):
    # Antes el lote solo se ofrecía sin opciones directas; ahora es una opción más, siempre visible.
    pedido = de("E1", distrito="DIST_NEBULA", canales_aceptables=TODOS_LOS_CANALES, motivo="social_support")
    opciones = client_fresco.post("/api/appointments/proposals?k=5", json=pedido).json()["opciones"]
    assert opciones and not any(o["tipo_opcion"] == "lote" for o in opciones)  # pares no está en lote
