"""El planificador de lotes: asigna en conjunto sin reservar, y mejora el orden de llegada cuando conviene."""

from aura.herramientas.estado_agenda import AgendaViva
from aura.servicio import ServicioAsignacion

BASE = {
    "motivo": "academic_pressure",
    "distrito": "DIST_GAIA",
    "grupo": "diurno",
    "canales_aceptables": ["digital"],
}


def solicitud(estudiante, dias, grupo="diurno"):
    return {
        **BASE,
        "estudiante_id": estudiante,
        "grupo": grupo,
        "franjas": [{"dia": d, "desde": "09:00", "hasta": "18:00"} for d in dias],
    }


def servicio_con_dos_cupos():
    """Deja libres solo dos cupos digitales de un mismo servicio: uno el primer lunes y otro el primer martes."""
    api = ServicioAsignacion()
    agenda = api._agenda
    digitales = [
        c for c in agenda.cupos
        if c.tipo == "counseling" and "digital" in c.canales and c.id in agenda.libres_base and c.fecha > agenda.hoy
    ]
    lunes = min((c for c in digitales if c.fecha.weekday() == 0), key=lambda c: (c.fecha, c.hora_inicio))
    martes = min(
        (c for c in digitales if c.fecha.weekday() == 1 and c.service_id == lunes.service_id and c.fecha > lunes.fecha),
        key=lambda c: (c.fecha, c.hora_inicio),
    )
    agenda.libres_base = {lunes.id, martes.id}
    return api, lunes, martes


def test_planificar_no_reserva_nada():
    api, lunes, martes = servicio_con_dos_cupos()
    plan = api.planificar_lote([solicitud("A", ["Mon", "Tue"]), solicitud("B", ["Mon"])])
    assert plan["n"] == 2 and api.citas() == []
    assert api._agenda.libres_ahora() == {lunes.id, martes.id}


def test_el_genetico_arregla_lo_que_el_orden_de_llegada_deja_sin_cupo():
    api, lunes, martes = servicio_con_dos_cupos()
    # A (flexible) llega primero y se llevaría el lunes; B solo puede el lunes.
    plan = api.planificar_lote([solicitud("A", ["Mon", "Tue"]), solicitud("B", ["Mon"])])
    assert plan["llegada"]["asignados"] == 1 and plan["llegada"]["desencuentros"] == 1
    assert plan["genetico"]["asignados"] == 2 and plan["genetico"]["desencuentros"] == 0
    assert plan["mejora_sobre_llegada"] is True and plan["sin_cupo"] == []
    cupos = {a["solicitud_id"].split("|")[1]: a["cupo_id"] for a in plan["asignaciones"]}
    assert cupos == {"B": lunes.id, "A": martes.id}
    assert plan["orden"][0].endswith("|B")  # B pasó al frente


def test_sin_competencia_el_resultado_es_el_del_orden_de_llegada():
    api = ServicioAsignacion()
    plan = api.planificar_lote([solicitud("A", ["Wed"]), solicitud("B", ["Wed"])])
    assert plan["genetico"]["asignados"] == plan["llegada"]["asignados"] == 2
    assert plan["genetico"]["objetivo"] <= plan["llegada"]["objetivo"]
    cupos = [a["cupo_id"] for a in plan["asignaciones"]]
    assert len(cupos) == len(set(cupos))  # nunca el mismo cupo dos veces


def test_una_solicitud_imposible_queda_sin_cupo_y_las_demas_siguen():
    api = ServicioAsignacion()
    imposible = {**solicitud("X", ["Sun"]), "franjas": [{"dia": "Sun", "desde": "03:00", "hasta": "04:00"}]}
    plan = api.planificar_lote([solicitud("A", ["Wed"]), imposible])
    assert plan["sin_cupo"] == ["002|X"] and plan["genetico"]["asignados"] == 1


def test_una_sola_solicitud_se_asigna_sin_genetico():
    api = ServicioAsignacion()
    plan = api.planificar_lote([solicitud("A", ["Wed"])])
    assert plan["n"] == 1 and len(plan["asignaciones"]) == 1 and plan["mejora_sobre_llegada"] is False


def test_las_propuestas_directas_pueden_apartar_servicios_en_lote():
    api = ServicioAsignacion()
    todo = api.proponer_opciones(solicitud("A", ["Wed"]), 20)["opciones"]
    servicios = {o["service_id"] for o in todo}
    assert len(servicios) > 1
    sin_uno = api.proponer_opciones(solicitud("A", ["Wed"]), 20, excluir_servicios={todo[0]["service_id"]})["opciones"]
    assert sin_uno and todo[0]["service_id"] not in {o["service_id"] for o in sin_uno}
