"""Costo de asignación y selección común de opciones libres."""

from collections.abc import Iterable, Set

from .datos import Opcion, Solicitud, Cupo
from .reglas import BETA_COSTO, P_CANAL


def costo_individual(
    opcion: Opcion, cupos_por_id: dict[str, Cupo], hoy, beta: float = BETA_COSTO
) -> float:
    """Calcula espera ajustada por canal y pérdida de afinidad para una opción."""
    cupo = cupos_por_id[opcion.cupo_id]
    dias_espera = (cupo.fecha - hoy).days
    return dias_espera / P_CANAL[opcion.canal] + beta * (1 - opcion.afinidad)


def mejores_opciones(
    solicitud: Solicitud,
    opciones_validas: Iterable[Opcion],
    cupos_ocupados: Set[str],
    k: int,
    *,
    cupos_por_id: dict[str, Cupo] | None = None,
    hoy=None,
    beta: float = BETA_COSTO,
) -> list[Opcion]:
    """Devuelve hasta k opciones libres de menor costo, con desempate estable."""
    if k <= 0:
        return []
    seleccionadas = []
    if hasattr(cupos_ocupados, "seleccionar_opciones"):
        return cupos_ocupados.seleccionar_opciones(solicitud, opciones_validas, k)
    if cupos_por_id is None or hoy is None:
        raise ValueError("Se requieren cupos_por_id y hoy para calcular costos")
    ordenadas = sorted(
        opciones_validas,
        key=lambda opcion: (
            costo_individual(opcion, cupos_por_id, hoy, beta),
            opcion.cupo_id,
            opcion.canal,
        ),
    )
    for opcion in ordenadas:
        if opcion.cupo_id in cupos_ocupados:
            continue
        seleccionadas.append(opcion)
        if len(seleccionadas) == k:
            break
    return seleccionadas
