"""Reglas en las herramientas y el backend: máximo de opciones, servicio pedido por nombre, equidad R7 y reglas visibles."""

import time

import pytest

from app.services.citas_service import CitasService
from app.services.errors import YaTieneCitaError
from app.services.lote_service import LoteService

LUNES_A_VIERNES = [{"dia": d, "desde": "09:00", "hasta": "18:00"} for d in ("Mon", "Tue", "Wed", "Thu", "Fri")]
TODOS_LOS_CANALES = ["digital", "phone", "in_person"]


def pedido(estudiante="E1", **cambios):
    base = {
        "estudiante_id": estudiante,
        "motivo": "career_concern",  # orientación vocacional: casi sin ocupación, nunca en lote
        "distrito": "DIST_GAIA",
        "grupo": "diurno",
        "franjas": LUNES_A_VIERNES,
        "canales_aceptables": TODOS_LOS_CANALES,
    }
    return {**base, **cambios}


def esperar(condicion, segundos=8):
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        if condicion():
            return True
        time.sleep(0.1)
    return False


# --- máximo de 3 opciones, servicio ideal primero -------------------------------------------------------------------


def test_nunca_devuelve_mas_de_3_opciones(client_fresco, sin_modo_lote):
    for k in (1, 3, 5, 20):
        opciones = client_fresco.post(f"/api/appointments/proposals?k={k}", json=pedido()).json()["opciones"]
        assert len(opciones) == min(k, 3)
    assert sin_modo_lote.parametros["max_opciones"] == 3  # el tope sale del YAML


def test_las_alternativas_afines_solo_completan_si_faltan(estado_fresco, sin_modo_lote):
    agenda = estado_fresco.motor._agenda
    libres = agenda.libres_ahora()

    def cupos(tipo, canal):
        return [c for c in agenda.cupos if c.id in libres and c.tipo == tipo and c.fecha.weekday() == 2
                and canal in c.canales and c.fecha > agenda.hoy and c.distrito == "DIST_GAIA"]

    ideal = cupos("counseling", "digital")[0]
    por_hora = {c.hora_inicio: c for c in cupos("peer_support", "phone")}  # dos horas distintas: dos opciones distintas
    par1, par2 = list(por_hora.values())[:2]
    agenda.libres_base = {ideal.id, par1.id, par2.id}
    miercoles = [{"dia": "Wed", "desde": "09:00", "hasta": "18:00"}]
    r = CitasService(estado_fresco).proponer(
        pedido(motivo="academic_pressure", franjas=miercoles, canales_aceptables=["digital", "phone"]), 3
    )
    assert [o["es_alternativa"] for o in r["opciones"]][0] is False  # primero, el servicio ideal
    assert r["opciones"][0]["tipo"] == "counseling"
    assert all(o["es_alternativa"] for o in r["opciones"][1:]) and len(r["opciones"]) == 3  # y solo después, las alternativas


def test_con_suficientes_del_servicio_ideal_no_aparecen_alternativas(client_fresco, sin_modo_lote):
    opciones = client_fresco.post("/api/appointments/proposals?k=3", json=pedido(motivo="academic_pressure")).json()["opciones"]
    assert len(opciones) == 3 and not any(o["es_alternativa"] for o in opciones)


# --- servicio pedido por nombre -------------------------------------------------------------------------------------


def test_service_id_preferido_pone_primero_las_opciones_de_ese_servicio(client_fresco, sin_modo_lote):
    r = client_fresco.post(
        "/api/appointments/proposals?k=3", json=pedido(service_id_preferido="Espacio Lumen Trayectoria")
    ).json()
    assert {o["service_id"] for o in r["opciones"]} == {"SRV_AE_006"}
    assert r["preferido"]["disponible"] is True and r["preferido"]["service_id"] == "SRV_AE_006"
    # por id y por una parte del nombre, sin tildes ni mayúsculas
    por_id = client_fresco.post("/api/appointments/proposals", json=pedido(service_id_preferido="SRV_AE_006")).json()
    assert {o["service_id"] for o in por_id["opciones"]} == {"SRV_AE_006"}
    parcial = client_fresco.post("/api/appointments/proposals", json=pedido(service_id_preferido="brujula trayectoria")).json()
    assert {o["service_id"] for o in parcial["opciones"]} == {"SRV_AE_003"}


def test_un_nombre_ambiguo_prefiere_el_servicio_del_tipo_que_necesita(client_fresco, sin_modo_lote):
    # «Brújula» es el nombre de tres servicios (orientación, pares, trayectoria): para una inquietud vocacional, la trayectoria
    r = client_fresco.post("/api/appointments/proposals", json=pedido(service_id_preferido="Brújula")).json()
    assert {o["service_id"] for o in r["opciones"]} == {"SRV_AE_003"}


def test_un_servicio_que_no_existe_se_dice_y_se_muestran_las_mejores_opciones(client_fresco, sin_modo_lote):
    r = client_fresco.post("/api/appointments/proposals", json=pedido(service_id_preferido="Espacio Fantasma")).json()
    assert r["preferido"] == {"consultado": "Espacio Fantasma", "encontrado": False}
    assert r["mensaje"].startswith("No encontré un servicio llamado «Espacio Fantasma»") and r["opciones"]


def test_servicio_pedido_sin_cupo_lo_dice_con_su_fecha_mas_cercana_y_la_mejor_del_mismo_tipo(estado_fresco, sin_modo_lote):
    agenda = estado_fresco.motor._agenda
    # Brújula Trayectoria no tiene cupos los martes; la persona solo puede los martes
    agenda.libres_base = {c for c in agenda.libres_base if not (agenda.cupo_por_id[c].service_id == "SRV_AE_003"
                                                                and agenda.cupo_por_id[c].fecha.weekday() == 1)}
    martes = [{"dia": "Tue", "desde": "09:00", "hasta": "18:00"}]
    r = CitasService(estado_fresco).proponer(pedido(franjas=martes, service_id_preferido="Espacio Brújula Trayectoria"), 3)
    p = r["preferido"]
    assert p["disponible"] is False and p["service_id"] == "SRV_AE_003"
    assert p["fecha_mas_cercana"] and p["fecha_mas_cercana"]["fecha"] > agenda.hoy.isoformat()
    otra = p["mejor_alternativa_mismo_tipo"]
    assert otra["tipo"] == "career_guidance" and otra["service_id"] != "SRV_AE_003" and otra["tipo_label"] == "Orientación vocacional"
    # el backend redacta la explicación: el modelo no la inventa
    assert "No hay cupos en Espacio Brújula Trayectoria" in r["mensaje"]
    assert "Su cupo más cercano es el" in r["mensaje"] and "La mejor opción de orientación vocacional en otro servicio" in r["mensaje"]
    assert r["opciones"] and all(o["service_id"] != "SRV_AE_003" for o in r["opciones"])


def test_toda_respuesta_trae_el_campo_mensaje(client_fresco, sin_modo_lote):
    normal = client_fresco.post("/api/appointments/proposals", json=pedido()).json()
    assert "mensaje" in normal and normal["mensaje"] is None
    vacio = client_fresco.post(
        "/api/appointments/proposals", json=pedido(franjas=[{"dia": "Sun", "desde": "03:00", "hasta": "04:00"}])
    ).json()
    assert vacio["opciones"] == [] and vacio["motivo_vacio"] == "sin_cupos_compatibles"
    assert vacio["mensaje"].startswith("No encontré cupos")


# --- R7: equidad ----------------------------------------------------------------------------------------------------


def reservar(client, estudiante, **cambios):
    propuesta = client.post("/api/appointments/proposals?k=3", json=pedido(estudiante, **cambios)).json()
    opcion = next(o for o in propuesta["opciones"] if o["tipo_opcion"] == "cupo")
    return client.post(
        "/api/appointments",
        json={"estudiante_id": estudiante, "opcion_id": opcion["opcion_id"], "servicio_ideal": propuesta["servicio_ideal"]},
    )


def test_r7_la_segunda_cita_del_mismo_tipo_se_rechaza_con_datos_y_mensaje_listo(client_fresco, sin_modo_lote):
    primera = reservar(client_fresco, "E_R7")
    assert primera.status_code == 201
    cita = primera.json()
    segunda = reservar(client_fresco, "E_R7")
    assert segunda.status_code == 409
    cuerpo = segunda.json()
    assert cuerpo["error"] == "ya_tiene_cita"
    assert cuerpo["cita"]["id"] == cita["id"] and cuerpo["cita"]["tipo"] == "career_guidance"
    assert cuerpo["cita"]["servicio_nombre"] == cita["servicio_nombre"] and cuerpo["cita"]["hora_inicio"]
    dia, numero = cuerpo["cita"]["dia_semana"], cuerpo["cita"]["fecha"].split("-")[2].lstrip("0")
    assert cuerpo["mensaje"] == (
        f"Ya tienes una cita de orientación vocacional el {dia} {numero} a las {cuerpo['cita']['hora_inicio']}. "
        "¿Quieres cambiarla por esta?"
    )
    # nada cambió: sigue una sola cita activa
    activas = [c for c in client_fresco.get("/api/appointments", params={"estudiante_id": "E_R7"}).json() if c["estado"] == "confirmada"]
    assert [c["id"] for c in activas] == [cita["id"]]


def test_r7_es_por_tipo_de_servicio_y_por_persona(client_fresco, sin_modo_lote):
    assert reservar(client_fresco, "E_A").status_code == 201
    assert reservar(client_fresco, "E_A", motivo="social_support").status_code == 201  # otro tipo: apoyo entre pares
    assert reservar(client_fresco, "E_B").status_code == 201  # otra persona, mismo tipo


def test_r7_confirmar_cambia_la_cita_anterior_por_la_nueva_en_una_sola_operacion(client_fresco, estado_fresco, sin_modo_lote):
    vieja = reservar(client_fresco, "E_CAMBIO").json()
    propuesta = client_fresco.post("/api/appointments/proposals?k=3", json=pedido("E_CAMBIO")).json()
    nueva_opcion = next(o for o in propuesta["opciones"] if o["tipo_opcion"] == "cupo")
    r = client_fresco.post(
        "/api/appointments",
        json={"estudiante_id": "E_CAMBIO", "opcion_id": nueva_opcion["opcion_id"], "reemplazar": True},
    )
    assert r.status_code == 201
    nueva = r.json()
    assert nueva["estado"] == "confirmada" and nueva["id"] != vieja["id"]
    estados = {c["id"]: c["estado"] for c in client_fresco.get("/api/appointments", params={"estudiante_id": "E_CAMBIO"}).json()}
    assert estados == {vieja["id"]: "cancelada", nueva["id"]: "confirmada"}
    # el cupo de la cita anterior quedó libre
    assert vieja["slot"]["id"] not in estado_fresco.motor._agenda.cupos_ocupados()


def test_r7_si_el_cupo_nuevo_ya_no_esta_la_cita_anterior_se_conserva(client_fresco, sin_modo_lote):
    vieja = reservar(client_fresco, "E_SEGURA").json()
    propuesta = client_fresco.post("/api/appointments/proposals?k=3", json=pedido("E_SEGURA")).json()
    opcion = next(o for o in propuesta["opciones"] if o["tipo_opcion"] == "cupo")
    assert client_fresco.post(
        "/api/appointments", json={"estudiante_id": "OTRA", "opcion_id": opcion["opcion_id"]}
    ).status_code == 201  # otra persona se lleva el cupo primero
    r = client_fresco.post(
        "/api/appointments", json={"estudiante_id": "E_SEGURA", "opcion_id": opcion["opcion_id"], "reemplazar": True}
    )
    assert r.status_code == 409 and r.json()["error"] == "cupo_ya_tomado"
    mia = client_fresco.get("/api/appointments", params={"estudiante_id": "E_SEGURA"}).json()
    assert [(c["id"], c["estado"]) for c in mia] == [(vieja["id"], "confirmada")]


def test_r7_una_cita_cancelada_no_cuenta(client_fresco, sin_modo_lote):
    cita = reservar(client_fresco, "E_LIBRE").json()
    client_fresco.delete(f"/api/appointments/{cita['id']}", params={"estudiante_id": "E_LIBRE"})
    assert reservar(client_fresco, "E_LIBRE").status_code == 201


def test_r7_tambien_vale_al_entrar_a_un_lote_y_el_cambio_se_hace_al_asignar(client_fresco, estado_fresco):
    estado_fresco.parametros["modo_lote_umbral_utilizacion"] = 1e6
    vieja = reservar(client_fresco, "E_LOTE_R7", motivo="academic_pressure").json()
    estado_fresco.parametros["modo_lote_umbral_utilizacion"] = 0.0  # ahora todo está en modo lote
    estado_fresco.parametros["lote"].update({"ventana_segundos": 1, "tamano_maximo": 5})
    citas = CitasService(estado_fresco)
    opcion = next(o for o in citas.proponer(pedido("E_LOTE_R7", motivo="academic_pressure"), 3)["opciones"] if o["tipo_opcion"] == "lote")
    with pytest.raises(YaTieneCitaError) as error:
        citas.reservar_opcion("E_LOTE_R7", opcion["opcion_id"], solicitud=pedido("E_LOTE_R7", motivo="academic_pressure"))
    assert error.value.mensaje.startswith("Ya tienes una cita de consejería")
    assert estado_fresco.lotes.abierto is None  # no llegó a entrar
    # confirma el cambio: queda pendiente y, al asignarle el lote la nueva, se cancela la anterior
    pendiente = citas.reservar_opcion(
        "E_LOTE_R7", opcion["opcion_id"], solicitud=pedido("E_LOTE_R7", motivo="academic_pressure"), reemplazar=True
    )
    assert pendiente["estado"] == "pendiente" and pendiente["lote"]["estado"] == "en_espera"
    assert esperar(lambda: estado_fresco.lotes.historial)
    estados = {c["id"]: c["estado"] for c in client_fresco.get("/api/appointments", params={"estudiante_id": "E_LOTE_R7"}).json()}
    assert estados[vieja["id"]] == "cancelada" and list(estados.values()).count("confirmada") == 1


# --- las reglas, a la vista -----------------------------------------------------------------------------------------


def test_la_pantalla_reglas_muestra_r7_y_el_umbral_del_lote(client):
    r = client.get("/api/coordinacion/reglas").json()
    assert r["equidad"]["max_citas_activas_por_tipo"] == 1
    assert r["modo_lote"]["umbral_pct"] == 75.0 and r["modo_lote"]["max_opciones"] == 3
    assert r["modo_lote"]["ventana_s"] == 30 and r["modo_lote"]["tamano_maximo"] == 5


def test_confirmacion_de_la_cita_lleva_la_linea_del_canal(client_fresco, sin_modo_lote):
    lineas = {}
    motivos = {"digital": "career_concern", "phone": "social_support", "in_person": "career_concern"}  # pares atiende por teléfono
    for i, canal in enumerate(("digital", "phone", "in_person")):
        estudiante = f"E_CANAL_{i}"
        propuesta = client_fresco.post(
            "/api/appointments/proposals?k=3", json=pedido(estudiante, motivo=motivos[canal], canales_aceptables=[canal])
        ).json()
        opcion = next(o for o in propuesta["opciones"] if o["canal"] == canal)
        cita = client_fresco.post("/api/appointments", json={"estudiante_id": estudiante, "opcion_id": opcion["opcion_id"]}).json()
        lineas[canal] = cita["aviso_canal"]
    assert lineas["digital"] == "El servicio te enviará el enlace a tu correo institucional antes de la cita."
    assert lineas["phone"] == "Te llamarán al número registrado."
    assert lineas["in_person"].startswith("Es presencial, en Espacio ") and "(distrito Gaia)" in lineas["in_person"]
