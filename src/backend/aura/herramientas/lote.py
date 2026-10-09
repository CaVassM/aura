"""Modo lote: asigna varias solicitudes en conjunto con el algoritmo genético (docs/como_funciona.md §7 y §8).

Planificar **no reserva nada**: calcula el mejor orden de prioridad para el grupo y qué cupo le toca a cada
solicitud. Quien llama (la plataforma) aplica las reservas. Si el genético no mejora el orden de llegada, se
conserva el orden de llegada.

La normalización de los cinco objetivos usa los *límites fijos* del experimento ("plan B", `z_plan_b`): una
calibración completa con cinco optimizaciones por lote sería demasiado lenta para hacerlo en vivo. En la utilización
de Z3 el denominador son los cupos que aún siguen libres en cada servicio.
"""

from collections import Counter
from time import perf_counter

from ..motor.baselines import orden_llegada, z_plan_b
from ..motor.datos import Solicitud
from ..motor.fitness import evaluar
from ..motor.genetico import genetico
from ..motor.reglas import precalcular_opciones, vectorizar_opciones
from .estado_agenda import AgendaViva


def _resumen(metricas: dict, objetivo: float) -> dict:
    return {
        "objetivo": round(objetivo, 4),
        "asignados": metricas["asignados"],
        "desencuentros": len(metricas["desencuentros"]),
        "espera_media": round(metricas["espera_promedio"], 2),
        "espera_diurnos": round(metricas["espera_diurnos"], 2),
        "espera_nocturnos": round(metricas["espera_nocturnos"], 2),
        "z": {k: round(metricas[k], 4) for k in ("Z1", "Z2", "Z3", "Z4", "Z5")},
    }


def planificar_lote(
    agenda: AgendaViva,
    solicitudes: list[Solicitud],
    poblacion: int = 40,
    generaciones: int = 100,
    semilla: int = 42,
) -> dict:
    """Plan de asignación conjunta. `solicitudes` debe traer ids únicos y en orden de llegada."""
    inicio = perf_counter()
    n = len(solicitudes)
    libres = agenda.libres_ahora()
    beta = float(agenda.parametros["beta"])
    opciones = precalcular_opciones(
        solicitudes, agenda.cupos, libres, agenda.hoy, beta, horizonte_dias=agenda.ventana_dias
    )
    opciones_vector, indice_vector = vectorizar_opciones(opciones, agenda.cupos)
    libres_por_servicio = Counter(agenda.cupo_por_id[c].service_id for c in libres)
    contexto = dict(
        solicitudes=solicitudes,
        opciones=opciones,
        cupos=agenda.cupos,
        servicios=agenda.servicios,
        libres=libres,
        hoy=agenda.hoy,
        beta=beta,
        horizonte_dias=agenda.ventana_dias,
        indice_cupos=agenda.cupo_por_id,
        liberados_servicio=dict(libres_por_servicio),
        opciones_vector=opciones_vector,
        indice_vector=indice_vector,
    )

    def evaluar_orden(orden):
        return evaluar(orden, **contexto)

    def objetivo(orden):
        return z_plan_b(evaluar_orden(orden)[0], n, agenda.ventana_dias)

    ids = [s.id for s in solicitudes]
    llegada = orden_llegada(solicitudes)
    mejor = list(llegada)
    if n >= 2:
        candidato, _, _ = genetico(ids, objetivo, poblacion, generaciones, semilla=semilla)
        if objetivo(candidato) < objetivo(llegada):
            mejor = candidato

    metricas_ga, asignaciones = evaluar_orden(mejor)
    metricas_llegada, _ = evaluar_orden(llegada)
    por_id = {s.id: s for s in solicitudes}
    plan = []
    for sid in mejor:
        if sid not in asignaciones:
            continue
        cupo, canal, afinidad = asignaciones[sid]
        servicio = agenda.servicio_por_id[cupo.service_id]
        plan.append(
            {
                "solicitud_id": sid,
                "opcion_id": f"{cupo.id}|{canal}",
                "cupo_id": cupo.id,
                "service_id": cupo.service_id,
                "servicio_nombre": servicio.nombre,
                "tipo": cupo.tipo,
                "distrito": cupo.distrito,
                "fecha": cupo.fecha.isoformat(),
                "hora_inicio": cupo.hora_inicio.isoformat(timespec="minutes"),
                "hora_fin": cupo.hora_fin.isoformat(timespec="minutes"),
                "canal": canal,
                "espera_dias": (cupo.fecha - agenda.hoy).days,
                "afinidad": afinidad,
                "es_alternativa": cupo.tipo != por_id[sid].servicio_ideal,
            }
        )
    return {
        "n": n,
        "orden": mejor,
        "asignaciones": plan,
        "sin_cupo": [sid for sid in mejor if sid not in asignaciones],
        "genetico": _resumen(metricas_ga, objetivo(mejor)),
        "llegada": _resumen(metricas_llegada, objetivo(llegada)),
        "mejora_sobre_llegada": objetivo(mejor) < objetivo(llegada),
        "poblacion": poblacion,
        "generaciones": generaciones,
        "tiempo_s": round(perf_counter() - inicio, 2),
    }
