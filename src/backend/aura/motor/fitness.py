"""Decodificador y funciones objetivo; todos los Z se minimizan."""

from collections import Counter, defaultdict
from statistics import mean, pvariance
from .datos import Cupo, Solicitud, Opcion
from .costo import mejores_opciones
from .reglas import BETA_COSTO, P_CANAL


class _DisponibilidadVectorial:
    """Selecciona opciones libres con los índices NumPy precalculados."""

    def __init__(self, reservados, opciones_vector, indice_vector):
        self.reservados = reservados
        self.opciones_vector = opciones_vector
        self.indice_vector = indice_vector

    def seleccionar_opciones(self, solicitud, opciones_validas, k):
        import numpy as np

        posiciones = self.opciones_vector[solicitud.id]
        libres = ~self.reservados[posiciones]
        indices = np.flatnonzero(libres)[:k]
        return [opciones_validas[int(i)] for i in indices]


def decodificar(
    orden,
    solicitudes,
    opciones,
    cupos,
    beta: float = BETA_COSTO,
    hoy=None,
    opciones_ordenadas=False,
    indice_cupos=None,
    opciones_vector=None,
    indice_vector=None,
):
    """Asigna codiciosamente la opción libre de menor costo por orden cromosómico."""
    if not opciones_ordenadas and hoy is None:
        raise ValueError(
            "Se requiere 'hoy' para calcular el costo con d desde la fecha base"
        )
    por_id = {s.id: s for s in solicitudes}
    cupo_id = indice_cupos or {c.id: c for c in cupos}
    usados = set()
    asignaciones = {}
    desencuentros = []
    reservados_vector = None
    if opciones_vector is not None:
        import numpy as np

        reservados_vector = np.zeros(len(indice_vector), dtype=np.bool_)
    for sid in orden:
        s = por_id[sid]
        ocupados = (
            _DisponibilidadVectorial(reservados_vector, opciones_vector, indice_vector)
            if opciones_vector is not None
            else usados
        )
        candidatas = mejores_opciones(
            s,
            opciones[sid],
            ocupados,
            1,
            cupos_por_id=cupo_id,
            hoy=hoy,
            beta=beta,
        )
        o = candidatas[0] if candidatas else None
        if o is None:
            desencuentros.append(
                {
                    "solicitud_id": sid,
                    "servicio_ideal": s.servicio_ideal,
                    "franjas": s.franjas,
                    "distrito": s.distrito,
                    "grupo": s.grupo,
                }
            )
            continue
        usados.add(o.cupo_id)
        asignaciones[sid] = (cupo_id[o.cupo_id], o.canal, o.afinidad)
        if reservados_vector is not None:
            reservados_vector[indice_vector[o.cupo_id]] = True
    assert len(usados) == len(asignaciones), "Un cupo fue asignado más de una vez"
    return asignaciones, desencuentros


def metricas(
    asignaciones,
    desencuentros,
    solicitudes,
    servicios,
    liberados_serv,
    hoy,
    horizonte_dias,
):
    """Calcula términos crudos Z1..Z5 y métricas legibles para el reporte."""
    n = len(solicitudes)
    Z1 = len(desencuentros)
    esperas = []
    coste = 0.0
    afin = 0.0
    por_grupo = defaultdict(list)
    usados_serv = Counter()
    serv_por_id = {s.service_id: s for s in servicios}
    solicitud_por_id = {s.id: s for s in solicitudes}
    for sid, (c, canal, a) in asignaciones.items():
        d = (c.fecha - hoy).days
        esperas.append(d)
        por_grupo[solicitud_por_id[sid].grupo].append(d)
        coste += d / P_CANAL[canal]
        afin += 1 - a
        usados_serv[c.service_id] += 1
    utilizacion = {
        sid: usados_serv[sid] / max(1, liberados_serv.get(sid, 0))
        for sid in serv_por_id
    }
    valores = list(utilizacion.values())
    Z3 = pvariance(valores) if valores else 0.0
    esperas_grupo = [mean(v) for v in por_grupo.values() if v]
    Z4 = max(esperas_grupo, default=0.0)
    return {
        "Z1": Z1,
        "Z2": coste,
        "Z3": Z3,
        "Z4": Z4,
        "Z5": afin,
        "asignados": len(asignaciones),
        "total": n,
        "pct_asignados": len(asignaciones) / n if n else 0,
        "espera_promedio": mean(esperas) if esperas else 0,
        "espera_diurnos": mean(por_grupo["diurno"]) if por_grupo["diurno"] else 0,
        "espera_nocturnos": mean(por_grupo["nocturno"]) if por_grupo["nocturno"] else 0,
        "utilizacion": utilizacion,
        "desencuentros": desencuentros,
    }


def evaluar(
    orden,
    solicitudes,
    opciones,
    cupos,
    servicios,
    libres,
    hoy,
    beta=BETA_COSTO,
    horizonte_dias=14,
    indice_cupos=None,
    liberados_servicio=None,
    opciones_vector=None,
    indice_vector=None,
):
    """Decodifica y calcula métricas en un solo paso."""
    asignaciones, fallidas = decodificar(
        orden,
        solicitudes,
        opciones,
        cupos,
        beta,
        hoy,
        opciones_ordenadas=True,
        indice_cupos=indice_cupos,
        opciones_vector=opciones_vector,
        indice_vector=indice_vector,
    )
    # Se cuentan los cupos efectivamente liberados por servicio usando el inventario.
    if liberados_servicio is None:
        cupo_por_id = indice_cupos or {c.id: c for c in cupos}
        liberados = {s.service_id: 0 for s in servicios}
        for cid in libres:
            liberados[cupo_por_id[cid].service_id] += 1
    else:
        liberados = liberados_servicio
    m = metricas(
        asignaciones, fallidas, solicitudes, servicios, liberados, hoy, horizonte_dias
    )
    return m, asignaciones
