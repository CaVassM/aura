"""El AppState es uno solo: lo que hace la vista del estudiante se ve en Coordinación."""

from datetime import date

from app.services.citas_service import CitasService

SOLICITUD = {
    "estudiante_id": "STU_TEST_1",
    "motivo": "social_support",
    "distrito": "DIST_GAIA",
    "grupo": "diurno",
    "franjas": [{"dia": d, "desde": "09:00", "hasta": "18:00"} for d in ("Mon", "Tue", "Wed", "Thu", "Fri")],
    "canales_aceptables": ["digital", "phone"],
}


def kpis(client):
    """KPIs de todo el horizonte de la agenda abierta."""
    return client.get("/api/coordinacion/resumen").json()["kpis"]


def test_reserva_por_la_capa_de_servicios_cambia_el_resumen(client_fresco, estado_fresco):
    servicio = CitasService(estado_fresco)  # lo mismo que usará la vista del estudiante
    propuesta = servicio.proponer(SOLICITUD, k=1)
    assert propuesta["opciones"]
    opcion = propuesta["opciones"][0]
    antes = kpis(client_fresco)
    cita = servicio.reservar("STU_TEST_1", opcion["opcion_id"])
    despues = kpis(client_fresco)
    assert despues["citas_agendadas"] == antes["citas_agendadas"] + 1
    assert despues["cupos_reservados"] == antes["cupos_reservados"] + 1
    servicio.cancelar(cita.id)
    assert kpis(client_fresco) == antes


def test_pedidos_en_vivo_usan_hoy_como_referencia(client_fresco, estado_fresco):
    hoy = estado_fresco.hoy
    propuesta = client_fresco.post("/api/appointments/proposals?k=20", json=SOLICITUD).json()
    assert propuesta["opciones"]
    assert all(o["fecha"] > hoy.isoformat() for o in propuesta["opciones"])
    assert all(o["dias_espera"] == (date.fromisoformat(o["fecha"]) - hoy).days for o in propuesta["opciones"])
    # Un cupo libre de la semana ya sembrada (anterior o igual a hoy) no se puede reservar en vivo.
    pasado = next(
        (c for c in estado_fresco.motor.cupos_liberados() if c["fecha"] <= hoy.isoformat() and not c["reservado"]),
        None,
    )
    if pasado:
        canal = estado_fresco.motor.servicio(pasado["service_id"])["canales"][0]
        r = client_fresco.post("/api/appointments", json={"estudiante_id": "S", "opcion_id": f"{pasado['cupo_id']}|{canal}"})
        assert r.status_code == 422
    cita = client_fresco.post("/api/appointments", json={"estudiante_id": "S", "opcion_id": propuesta["opciones"][0]["opcion_id"]})
    assert cita.status_code == 201


def test_reserva_en_vivo_con_servicio_ideal_cuenta_como_alternativa(client_fresco, estado_fresco):
    """Si el estudiante envía el servicio ideal de la propuesta, la cita entra en la demanda desviada."""
    antes = client_fresco.get("/api/coordinacion/resumen").json()["kpis"]["atendidos_alternativa"]
    propuesta = client_fresco.post("/api/appointments/proposals?k=20", json=SOLICITUD).json()
    alternativa = next((o for o in propuesta["opciones"] if o["es_alternativa"]), None)
    if alternativa is None:  # sin alternativa disponible en esta agenda: nada que comprobar
        return
    r = client_fresco.post("/api/appointments", json={
        "estudiante_id": "S", "opcion_id": alternativa["opcion_id"], "servicio_ideal": propuesta["servicio_ideal"]})
    assert r.status_code == 201
    despues = client_fresco.get("/api/coordinacion/resumen").json()["kpis"]["atendidos_alternativa"]
    assert despues == antes + 1


def test_desencuentro_registrado_por_el_motor_aparece_en_coordinacion(client_fresco, estado_fresco):
    antes = client_fresco.get("/api/coordinacion/desencuentros").json()["total"]
    resultado = estado_fresco.motor.registrar_desencuentro({**SOLICITUD, "motivo": "career_concern"})
    assert resultado["ok"]
    datos = client_fresco.get("/api/coordinacion/desencuentros", params={"motivo": "career_concern"}).json()
    assert datos["total"] == antes + 1
    assert resultado["registro_id"] in {i["id"] for i in datos["items"]}
    assert kpis(client_fresco)["desencuentros"] == antes + 1


def test_flujo_http_del_estudiante(client_fresco):
    propuesta = client_fresco.post("/api/appointments/proposals?k=1", json=SOLICITUD)
    assert propuesta.status_code == 200
    antes = kpis(client_fresco)
    opcion = propuesta.json()["opciones"][0]["opcion_id"]
    reserva = client_fresco.post("/api/appointments", json={"estudiante_id": "STU_TEST_1", "opcion_id": opcion})
    assert reserva.status_code == 201
    cita = reserva.json()
    mias = client_fresco.get("/api/appointments", params={"estudiante_id": "STU_TEST_1"}).json()
    assert [c["id"] for c in mias] == [cita["id"]]
    assert kpis(client_fresco)["citas_agendadas"] == antes["citas_agendadas"] + 1
    otra = client_fresco.post("/api/appointments", json={"estudiante_id": "OTRO", "opcion_id": opcion})
    assert otra.status_code == 409 and otra.json()["error"] == "cupo_ya_tomado"
    cancelada = client_fresco.delete(f"/api/appointments/{cita['id']}")
    assert cancelada.json()["estado"] == "cancelada"
    assert kpis(client_fresco) == antes
    assert client_fresco.delete("/api/appointments/CITA-9999999").status_code == 404


def test_solicitud_invalida_da_422(client_fresco):
    respuesta = client_fresco.post("/api/appointments/proposals", json={**SOLICITUD, "motivo": "no_existe"})
    assert respuesta.status_code == 422


def test_el_tipo_acompana_al_nombre_en_la_vista_del_estudiante(client_fresco):
    propuesta = client_fresco.post("/api/appointments/proposals?k=1", json=SOLICITUD).json()
    assert propuesta["opciones"][0]["tipo_label"] == "Apoyo entre pares"
    opcion = propuesta["opciones"][0]["opcion_id"]
    cita = client_fresco.post("/api/appointments", json={"estudiante_id": "S", "opcion_id": opcion}).json()
    assert cita["tipo_label"] == "Apoyo entre pares"


def test_catalogo_del_estudiante(client):
    servicios = client.get("/api/services").json()
    assert len(servicios) == 15 and all(s["tipo_label"] for s in servicios)
    assert client.get(f"/api/services/{servicios[0]['service_id']}/slots").status_code == 200
    assert client.get("/api/services/NO_EXISTE/slots").status_code == 404


def test_reiniciar_restaura_la_demo(client_fresco, estado_fresco):
    servicio = CitasService(estado_fresco)
    opcion = servicio.proponer(SOLICITUD, k=1)["opciones"][0]
    sembrado = kpis(client_fresco)
    servicio.reservar("STU_TEST_1", opcion["opcion_id"])
    assert kpis(client_fresco)["citas_agendadas"] == sembrado["citas_agendadas"] + 1
    respuesta = client_fresco.post("/api/demo/reiniciar")
    assert respuesta.status_code == 200 and respuesta.json()["etiqueta"].startswith("Simulación")
    assert kpis(client_fresco) == sembrado  # mismo objeto de estado, contenido reconstruido
