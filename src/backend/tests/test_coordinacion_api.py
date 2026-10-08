"""Endpoints de Coordinación: forma de la respuesta y coherencia con el AppState."""

import json
from datetime import date, timedelta

import pytest

from aura.herramientas.configuracion import cargar_yaml


def test_salud(client):
    assert client.get("/api/salud").json() == {"ok": True}


def test_demo_estado(client, estado_sembrado):
    datos = client.get("/api/demo/estado").json()
    assert datos["hoy"] == estado_sembrado.hoy.isoformat()
    assert date.fromisoformat(datos["semana_inicio"]).weekday() == 0  # lunes
    assert date.fromisoformat(datos["semana_fin"]).weekday() == 6  # domingo
    assert datos["semana_fin"] == datos["hoy"]  # la demo corre el último día de la semana
    assert datos["escenario"] == cargar_yaml("parametros.yaml")["demo"]["escenario"]
    if datos["escenario"] == "x6":
        assert datos["etiqueta"] == (
            "Simulación · escenario de estrés en semana de evaluaciones (demanda ×6)"
            " · 10 % vespertinos que trabajan"
        )
    assert datos["etiqueta"].startswith("Simulación")
    hoy = estado_sembrado.hoy
    primer_pedido = hoy - timedelta(days=hoy.weekday())
    fin = hoy + timedelta(days=7 * estado_sembrado.parametros["horizonte_semanas"])
    assert date.fromisoformat(datos["agenda_inicio"]) == primer_pedido + timedelta(days=1)  # toda la agenda
    assert date.fromisoformat(datos["agenda_fin"]) == fin
    assert date.fromisoformat(datos["agenda_abierta_inicio"]) == hoy + timedelta(days=1)  # lo reservable
    assert date.fromisoformat(datos["agenda_abierta_fin"]) == fin
    assert "% vespertinos que trabajan" in datos["etiqueta"]
    assert datos["umbrales_nivel"] == estado_sembrado.parametros["coordinacion"]["nivel_ocupacion"]


def test_resumen_es_coherente_con_el_estado(client, estado_sembrado):
    datos = client.get("/api/coordinacion/resumen").json()
    k, servicios = datos["kpis"], datos["servicios"]
    hoy = estado_sembrado.hoy.isoformat()
    assert len(servicios) == len(estado_sembrado.motor.servicios())
    # Cupos liberados y ocupados: solo la agenda abierta (posterior a hoy).
    abiertos = [c for c in estado_sembrado.motor.cupos_liberados() if c["fecha"] > hoy]
    assert k["cupos_liberados"] == len(abiertos) == sum(s["cupos_liberados"] for s in servicios)
    assert k["cupos_reservados"] == sum(c["reservado"] for c in abiertos) == sum(s["cupos_reservados"] for s in servicios)
    assert k["ocupacion_pct"] == pytest.approx(100 * k["cupos_reservados"] / k["cupos_liberados"], abs=0.05)
    # Citas, espera y desencuentros: todo lo sembrado en la semana de pedidos.
    citas = estado_sembrado.motor.citas()
    assert k["citas_agendadas"] == len(citas) > k["cupos_reservados"]
    assert k["espera_media_dias"] == pytest.approx(sum(c["dias_espera"] for c in citas) / len(citas), abs=0.05)
    assert k["desencuentros"] == len(estado_sembrado.desencuentros)
    assert k["espera_linea_base_dias"] == pytest.approx(estado_sembrado.espera_linea_base_dias, abs=0.005)
    assert datos["agenda_abierta"]["desde"] == (estado_sembrado.hoy + timedelta(days=1)).isoformat()
    umbrales = estado_sembrado.parametros["coordinacion"]["nivel_ocupacion"]
    for s in servicios:
        esperado = (
            "baja" if s["ocupacion_pct"] < umbrales["baja_menor_que"]
            else "alta" if s["ocupacion_pct"] > umbrales["alta_mayor_que"]
            else "media"
        )  # fmt: skip
        assert s["nivel"] == esperado
        assert s["tipo_label"]


def test_resumen_acepta_filtro_de_semana(client, estado_sembrado):
    todo = client.get("/api/coordinacion/resumen").json()
    hoy = estado_sembrado.hoy
    semanas = [
        client.get("/api/coordinacion/resumen", params={"semana": (hoy + timedelta(days=d)).isoformat()}).json()
        for d in (1, 8)  # las dos semanas de la agenda abierta
    ]
    assert sum(s["kpis"]["cupos_liberados"] for s in semanas) == todo["kpis"]["cupos_liberados"]
    assert sum(s["kpis"]["cupos_reservados"] for s in semanas) == todo["kpis"]["cupos_reservados"]
    # Una semana ya pasada no tiene cupos liberados que contar, pero sí las citas solicitadas en ella.
    pasada = client.get("/api/coordinacion/resumen", params={"semana": hoy.isoformat()}).json()
    assert pasada["kpis"]["cupos_liberados"] == 0 and pasada["kpis"]["ocupacion_pct"] == 0
    assert pasada["kpis"]["citas_agendadas"] == todo["kpis"]["citas_agendadas"]


def test_demanda_desviada_a_alternativas_afines(client, estado_sembrado):
    """Pedidos atendidos en un tipo distinto del ideal, por tipo y a cuál; KPI global = suma."""
    citas = estado_sembrado.motor.citas()
    resumen = client.get("/api/coordinacion/resumen").json()
    alternativas = [c for c in citas if c["servicio_ideal"] != c["tipo"]]
    assert resumen["kpis"]["atendidos_alternativa"] == len(alternativas) > 0
    filas = {d["ideal"]: d for d in resumen["demanda_por_tipo"]}
    assert sum(d["atendidos_con_alternativa"] for d in filas.values()) == len(alternativas)
    assert sum(d["atendidos_en_su_tipo"] + d["atendidos_con_alternativa"] for d in filas.values()) == len(citas)
    assert sum(d["sin_cupo"] for d in filas.values()) == resumen["kpis"]["desencuentros"]
    for d in filas.values():
        assert d["pedidos"] == d["atendidos_en_su_tipo"] + d["atendidos_con_alternativa"] + d["sin_cupo"]
        assert sum(x["cantidad"] for x in d["destinos"]) == d["atendidos_con_alternativa"]
        assert all(x["tipo"] != d["ideal"] and x["tipo_label"] for x in d["destinos"])
    # Detalle de un servicio: su tipo y lo que recibió como alternativa de otros tipos.
    pares = next(s for s in resumen["servicios"] if s["tipo"] == "peer_support")
    det = client.get(f"/api/coordinacion/servicios/{pares['service_id']}").json()
    assert det["demanda_del_tipo"] == filas["peer_support"]
    recibidos = [c for c in citas if c["service_id"] == pares["service_id"] and c["servicio_ideal"] != "peer_support"]
    assert det["recibidos_como_alternativa"]["cantidad"] == len(recibidos)


def test_cada_pedido_toma_cupos_dentro_de_su_ventana(client, estado_sembrado):
    """Ventana de cada pedido: de su fecha de solicitud + 1 a su fecha + 14 días (como wait_days de D2)."""
    dias = 7 * estado_sembrado.parametros["horizonte_semanas"]
    citas = estado_sembrado.motor.citas()
    assert citas
    for c in citas:
        solicitud, cupo = date.fromisoformat(c["fecha_solicitud"]), date.fromisoformat(c["fecha"])
        assert solicitud < cupo <= solicitud + timedelta(days=dias)
        assert (cupo - solicitud).days == c["dias_espera"]
        assert solicitud <= estado_sembrado.hoy
    kpi = client.get("/api/coordinacion/resumen").json()["kpis"]["espera_media_dias"]
    assert kpi == pytest.approx(sum(c["dias_espera"] for c in citas) / len(citas), abs=0.05)


def test_embudo_de_cupos_por_servicio(client, estado_sembrado):
    """capacidad (prorrateada a la agenda abierta) ≥ libres ≥ liberados ≥ reservados; suma = KPI de la red."""
    resumen = client.get("/api/coordinacion/resumen").json()
    estado = client.get("/api/demo/estado").json()
    pcts = estado_sembrado.parametros
    for s in resumen["servicios"]:
        assert s["capacidad_agenda_abierta"] >= s["libres_agenda_abierta"] >= s["cupos_liberados"] >= s["cupos_reservados"] >= 0
        # 2 semanas completas de agenda abierta: la capacidad es 2 × la capacidad semanal de D6.
        assert s["capacidad_agenda_abierta"] == s["capacidad_semanal"] * pcts["horizonte_semanas"]
    k = resumen["kpis"]
    for clave in ("capacidad_agenda_abierta", "libres_agenda_abierta", "cupos_liberados", "cupos_reservados"):
        assert k[clave] == sum(s[clave] for s in resumen["servicios"])
    # El estado de la demo trae los porcentajes que usa el glosario.
    assert estado["ocupacion_inicial_pct"] == pytest.approx(100 * pcts["ocupacion_inicial"])
    assert estado["fraccion_liberada_pct"] == pytest.approx(100 * estado_sembrado.escenario["fraccion_liberada"])
    assert estado["agenda_abierta_semanas"] == pcts["horizonte_semanas"]
    assert (estado["pedidos_desde"], estado["pedidos_hasta"]) == (resumen["pedidos"]["desde"], resumen["pedidos"]["hasta"])
    assert estado["espera_linea_base_dias"] == resumen["kpis"]["espera_linea_base_dias"]
    # Los mismos campos llegan en el GeoJSON y el detalle trae el embudo por día.
    props = client.get("/api/coordinacion/servicios").json()["features"][0]["properties"]
    assert props["capacidad_agenda_abierta"] and props["libres_agenda_abierta"] >= props["cupos_liberados"]
    det = client.get(f"/api/coordinacion/servicios/{props['service_id']}").json()
    assert sum(d["liberados"] for d in det["cupos_por_dia"]) == len(estado_sembrado.motor.cupos_liberados(props["service_id"]))


def test_servicios_filtran_por_distrito_y_nivel(client):
    todos = client.get("/api/coordinacion/servicios").json()["features"]
    distrito = todos[0]["properties"]["distrito"]
    por_distrito = client.get("/api/coordinacion/servicios", params={"distrito": distrito}).json()["features"]
    assert por_distrito and all(f["properties"]["distrito"] == distrito for f in por_distrito)
    nivel = todos[0]["properties"]["nivel"]
    por_nivel = client.get("/api/coordinacion/servicios", params={"nivel": nivel}).json()["features"]
    assert por_nivel and all(f["properties"]["nivel"] == nivel for f in por_nivel)
    assert client.get("/api/coordinacion/servicios", params={"nivel": "extrema"}).status_code == 422


def test_servicios_geojson(client, estado_sembrado):
    datos = client.get("/api/coordinacion/servicios").json()
    assert datos["type"] == "FeatureCollection"
    assert len(datos["features"]) == 15
    d6 = json.loads((estado_sembrado.settings.data_dir / "D6_services_map.geojson").read_text(encoding="utf-8"))
    geometrias = {f["id"]: f["geometry"] for f in d6["features"]}
    for f in datos["features"]:
        p = f["properties"]
        assert f["geometry"] == geometrias[f["id"]]
        assert 0 <= p["pos"]["x"] <= 1 and 0 <= p["pos"]["y"] <= 1
        assert p["alta_demanda"] == (p["nivel"] == "alta")
        assert p["horario_texto"] and p["canales_label"] and p["direccion"] is None
    xs = [f["properties"]["pos"]["x"] for f in datos["features"]]
    assert min(xs) == 0 and max(xs) == 1


def test_servicios_filtros(client):
    todos = client.get("/api/coordinacion/servicios").json()["features"]
    pares = client.get("/api/coordinacion/servicios", params={"tipo": "peer_support"}).json()["features"]
    assert pares and all(f["properties"]["tipo"] == "peer_support" for f in pares)
    telefono = client.get("/api/coordinacion/servicios", params={"canal": "phone"}).json()["features"]
    assert telefono and all("phone" in f["properties"]["canales"] for f in telefono)
    altos = client.get("/api/coordinacion/servicios", params={"solo_alta_demanda": "true"}).json()["features"]
    assert len(altos) == sum(f["properties"]["alta_demanda"] for f in todos)


def test_servicio_detalle(client, estado_sembrado):
    mapa = client.get("/api/coordinacion/servicios").json()["features"]
    props = next(f["properties"] for f in mapa if f["properties"]["tipo"] == "career_guidance")
    datos = client.get(f"/api/coordinacion/servicios/{props['service_id']}").json()
    assert datos["servicio"]["service_id"] == props["service_id"]
    horizonte = estado_sembrado.motor.cupos_liberados(props["service_id"])
    assert sum(d["liberados"] for d in datos["cupos_por_dia"]) == len(horizonte)
    assert sum(d["reservados"] for d in datos["cupos_por_dia"]) == sum(c["reservado"] for c in horizonte)
    for d in datos["desencuentros_recientes"]:
        assert d["servicio_ideal"] == props["tipo"] and d["distrito"] == props["distrito"]
    assert client.get("/api/coordinacion/servicios/NO_EXISTE").status_code == 404


def test_desencuentros_paginacion_y_agregados(client, estado_sembrado):
    datos = client.get("/api/coordinacion/desencuentros", params={"tamano": 5}).json()
    total = len(estado_sembrado.desencuentros)
    assert datos["total"] == datos["filtrados"] == total > 0
    assert datos["paginas"] == -(-total // 5) and len(datos["items"]) == min(5, total)
    item = datos["items"][0]
    assert item["motivo_label"] and item["servicio_ideal_label"] and item["grupo"] == "nocturno"
    # La franja se muestra tal cual la declaró la solicitud (vespertino que trabaja: 19–21).
    assert (item["franja"]["desde"], item["franja"]["hasta"]) == ("19:00", "21:00")
    # Matriz distrito × servicio ideal: filas = distritos de D6, columnas = tipos; totales por fila y columna.
    m = datos["matriz_distrito_servicio"]
    assert len(m["distritos"]) == 5 and [c["tipo"] for c in m["servicios"]] == ["counseling", "peer_support", "career_guidance"]
    assert m["total"] == total == sum(map(sum, m["celdas"]))
    assert m["total_filas"] == [sum(f) for f in m["celdas"]]
    assert m["total_columnas"] == [sum(f[j] for f in m["celdas"]) for j in range(3)]
    # Todos los desencuentros simulados declaran la misma franja: 19–21, lunes a viernes.
    fp = datos["franja_principal"]
    assert fp["porcentaje"] == 100.0 and fp["texto"] == "entre 19:00 y 21:00, lunes a viernes"
    assert 0 < datos["insight"]["porcentaje"] <= 100 and datos["insight"]["texto"]


def test_desencuentros_filtros_y_pagina_dos(client):
    base = client.get("/api/coordinacion/desencuentros", params={"tamano": 3, "pagina": 2}).json()
    assert base["pagina"] == 2 and len(base["items"]) <= 3
    motivo = base["items"][0]["motivo"]
    filtrado = client.get("/api/coordinacion/desencuentros", params={"motivo": motivo}).json()
    assert 0 < filtrado["filtrados"] <= filtrado["total"]
    assert all(i["motivo"] == motivo for i in filtrado["items"])
    assert filtrado["matriz_distrito_servicio"]["total"] == filtrado["filtrados"]  # la matriz respeta los filtros
    vacio = client.get("/api/coordinacion/desencuentros", params={"grupo": "diurno"}).json()
    assert vacio["filtrados"] == 0 and vacio["items"] == []
    assert vacio["franja_principal"] is None and vacio["matriz_distrito_servicio"]["total"] == 0
    # El hallazgo principal no depende de los filtros; el del filtro va aparte.
    total = client.get("/api/coordinacion/desencuentros").json()
    assert total["insight_filtro"] is None
    assert filtrado["insight"] == vacio["insight"] == total["insight"] and total["insight"]["grupo"] == "nocturno"
    assert filtrado["insight_filtro"]["texto"] and vacio["insight_filtro"]["grupo"] is None


def test_desencuentros_csv(client):
    respuesta = client.get("/api/coordinacion/desencuentros.csv")
    assert respuesta.headers["content-type"].startswith("text/csv")
    assert "attachment" in respuesta.headers["content-disposition"]
    filas = respuesta.content.decode("utf-8-sig").splitlines()
    total = client.get("/api/coordinacion/desencuentros").json()["total"]
    assert filas[0].startswith("id,fecha,motivo,motivo_label") and len(filas) == total + 1
    filtrado = client.get("/api/coordinacion/desencuentros.csv", params={"grupo": "diurno"})
    assert len(filtrado.content.decode("utf-8-sig").splitlines()) == 1


def test_reglas(client, estado_sembrado):
    r = client.get("/api/coordinacion/reglas").json()
    for bloque in ("motivo_servicio", "afinidad", "aviso", "p_asistencia", "pesos"):
        assert isinstance(r[bloque]["provisional"], bool)
    assert r["pesos"]["provisional"] is True and r["aviso"]["provisional"] is False
    assert sum(t["peso"] for t in r["pesos"]["terminos"]) == pytest.approx(1.0)
    assert r["aviso"]["solo_semanas_evaluacion"] is True and len(r["aviso"]["senales"]) == 4
    # Nada en inglés a la vista: los valores técnicos se traducen.
    s1 = r["aviso"]["senales"][0]
    assert s1["umbral"] == ["medium", "high"] and s1["umbral_texto"] == "media o alta"
    assert "dropout_alert" not in s1["descripcion"] and "media o alta" in s1["descripcion"]
    textos = " ".join(f'{s["descripcion"]} {s["umbral_texto"]}' for s in r["aviso"]["senales"])
    assert not any(w in textos for w in ("medium", "high", "low", "grade_change"))
    assert r["afinidad"]["minimo_alternativa"] == estado_sembrado.parametros["umbral_afinidad"]
    assert all(len(f["valores"]) == 3 for f in r["afinidad"]["matriz"])
    assert {c["canal_label"] for c in r["p_asistencia"]["canales"]} == {"Videollamada", "Teléfono", "Presencial"}
