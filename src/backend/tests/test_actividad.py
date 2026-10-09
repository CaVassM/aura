"""Registro en vivo de lo nuevo: solo citas y desencuentros posteriores a la siembra, con su flujo SSE."""

import asyncio
import json

from app.api.actividad import flujo_actividad
from app.services.citas_service import CitasService

SOLICITUD = {
    "estudiante_id": "STU_VIVO_1",
    "motivo": "social_support",
    "distrito": "DIST_GAIA",
    "grupo": "diurno",
    "franjas": [{"dia": d, "desde": "09:00", "hasta": "21:00"} for d in ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat")],
    "canales_aceptables": ["digital", "phone"],
}


def actividad(client, desde=0):
    return client.get("/api/coordinacion/actividad", params={"desde": desde}).json()


def reservar(client, estudiante="STU_VIVO_1"):
    propuesta = client.post("/api/appointments/proposals?k=1", json={**SOLICITUD, "estudiante_id": estudiante}).json()
    opcion = propuesta["opciones"][0]
    r = client.post(
        "/api/appointments",
        json={"estudiante_id": estudiante, "opcion_id": opcion["opcion_id"], "servicio_ideal": propuesta["servicio_ideal"]},
    )
    assert r.status_code == 201
    return r.json()


def test_la_siembra_no_llena_el_registro(client_fresco, estado_fresco):
    assert estado_fresco.motor.citas()  # la demo viene con cientos de citas sembradas…
    cuerpo = actividad(client_fresco)
    assert cuerpo["eventos"] == [] and cuerpo["ultimo_id"] == 0 and cuerpo["epoca"]  # …y ninguna entra al registro


def test_reservar_deja_un_evento_con_la_ocupacion_del_servicio(client_fresco, estado_fresco):
    cita = reservar(client_fresco)
    [e] = actividad(client_fresco)["eventos"]
    assert e["id"] == 1 and e["tipo"] == "cita_reservada" and e["origen"] == "api"
    assert e["estudiante_id"] == "STU_VIVO_1"
    assert e["fecha_solicitud"] == estado_fresco.hoy.isoformat()  # fecha simulada de la demo
    assert e["registrado_en"].endswith("+00:00")
    assert e["servicio"]["nombre"] == cita["servicio_nombre"] and e["servicio"]["tipo_label"]
    assert e["cita"]["cita_id"] == cita["id"] and e["cita"]["canal_label"] and e["cita"]["fecha"] > e["fecha_solicitud"]
    oc = e["ocupacion"]
    assert oc["pct"] > oc["antes_pct"] and oc["nivel"] in {"baja", "media", "alta"}
    assert oc["reservados"] <= oc["liberados"]


def test_cancelar_deja_un_evento_una_sola_vez(client_fresco):
    cita = reservar(client_fresco)
    for _ in range(2):  # cancelar de nuevo no repite el aviso
        assert client_fresco.delete(f"/api/appointments/{cita['id']}").status_code == 200
    eventos = actividad(client_fresco)["eventos"]
    assert [e["tipo"] for e in eventos] == ["cita_reservada", "cita_cancelada"]
    reservada, cancelada = eventos
    assert cancelada["ocupacion"]["pct"] < reservada["ocupacion"]["pct"]
    assert cancelada["ocupacion"]["antes_pct"] == reservada["ocupacion"]["pct"]


def test_desde_devuelve_solo_lo_nuevo(client_fresco):
    reservar(client_fresco, "STU_A")
    reservar(client_fresco, "STU_B")
    todo = actividad(client_fresco)
    assert [e["id"] for e in todo["eventos"]] == [1, 2] and todo["ultimo_id"] == 2
    assert [e["estudiante_id"] for e in actividad(client_fresco, desde=1)["eventos"]] == ["STU_B"]
    assert actividad(client_fresco, desde=2)["eventos"] == []


def test_el_desencuentro_se_registra_con_etiquetas_legibles(client_fresco, estado_fresco):
    sin_cupos = {**SOLICITUD, "franjas": [{"dia": "Sun", "desde": "03:00", "hasta": "04:00"}], "canales_aceptables": ["phone"]}
    resultado = CitasService(estado_fresco).registrar_desencuentro(sin_cupos, origen="chat")
    assert resultado["ok"]
    [e] = actividad(client_fresco)["eventos"]
    assert e["tipo"] == "desencuentro" and e["origen"] == "chat" and e["servicio"] is None
    d = e["desencuentro"]
    assert d["registro_id"] == resultado["registro_id"] and d["franjas"] == "domingo 03:00–04:00"
    assert d["motivo_label"] and d["servicio_ideal_label"] and d["grupo_label"] == "Diurno"


def test_reiniciar_la_demo_vacia_el_registro_y_cambia_la_epoca(client_fresco):
    reservar(client_fresco)
    antes = actividad(client_fresco)
    assert client_fresco.post("/api/demo/reiniciar").status_code == 200
    despues = actividad(client_fresco)
    assert despues["eventos"] == [] and despues["epoca"] != antes["epoca"]


# --- flujo SSE (se prueba el generador: un stream infinito no se puede leer entero con TestClient) ---


async def tomar(generador, cuantos, tiempo=3):
    salida = []
    async def leer():
        async for trozo in generador:
            salida.append(trozo)
            if len(salida) == cuantos:
                return
    await asyncio.wait_for(leer(), tiempo)
    return salida


def cuerpo_sse(trozo):
    return json.loads(trozo.split("data: ", 1)[1])


def test_sse_manda_inicio_y_luego_cada_evento_nuevo(estado_fresco):
    async def escenario():
        gen = flujo_actividad(estado_fresco, desde=0)
        retry, inicio = await tomar(gen, 2)
        assert retry.startswith("retry:") and cuerpo_sse(inicio)["reinicio"] is False
        servicio = CitasService(estado_fresco)
        opcion = servicio.proponer(SOLICITUD, 1)["opciones"][0]
        servicio.reservar("STU_SSE", opcion["opcion_id"])
        trozo = await tomar(gen, 1)
        assert trozo[0].startswith("id: 1\nevent: actividad\n")
        assert cuerpo_sse(trozo[0])["estudiante_id"] == "STU_SSE"
        await gen.aclose()
    asyncio.run(escenario())


def test_sse_reconecta_sin_repetir_lo_ya_visto(estado_fresco):
    servicio = CitasService(estado_fresco)
    for n in range(2):
        servicio.reservar(f"STU_{n}", servicio.proponer(SOLICITUD, 1)["opciones"][0]["opcion_id"])

    async def escenario():
        gen = flujo_actividad(estado_fresco, desde=1)
        _, inicio, evento = await tomar(gen, 3)
        assert cuerpo_sse(evento)["id"] == 2  # el 1 ya lo tenía
        await gen.aclose()
    asyncio.run(escenario())


def test_sse_avisa_si_el_cliente_viene_de_otra_ejecucion(estado_fresco):
    async def escenario():
        gen = flujo_actividad(estado_fresco, desde=50)  # más alto que lo que existe: el backend se reinició
        _, inicio = await tomar(gen, 2)
        assert cuerpo_sse(inicio)["reinicio"] is True
        await gen.aclose()
    asyncio.run(escenario())


def test_sse_avisa_cuando_se_reinicia_la_demo_con_el_flujo_abierto(estado_fresco, settings):
    from app.services.siembra_service import crear_estado_sembrado

    async def escenario():
        gen = flujo_actividad(estado_fresco, desde=0)
        await tomar(gen, 2)
        estado_fresco.reemplazar_por(crear_estado_sembrado(settings))
        [aviso] = await tomar(gen, 1)
        assert "event: reinicio" in aviso
        await gen.aclose()
    asyncio.run(escenario())


def test_sse_manda_ping_para_mantener_la_conexion(estado_fresco):
    async def escenario():
        gen = flujo_actividad(estado_fresco, desde=0, ping_cada_s=0)
        trozos = await tomar(gen, 3)
        assert trozos[2] == ": ping\n\n"
        await gen.aclose()
    asyncio.run(escenario())
