"""Definiciones de cupos, ocupación y rangos de fechas, compartidas por resumen y servicios.

- **Agenda** (`agenda_desde`–`agenda_hasta`): todo lo generado, del día siguiente al primer
  pedido hasta hoy + horizonte.
- **Agenda abierta** (`hoy + 1`–`agenda_hasta`): lo que todavía se puede reservar.
- **Embudo de cupos** (capacidad → libres → liberados → reservados), **cupos liberados** y **ocupación** (cupos reservados / cupos liberados × 100) se miden solo sobre
  la agenda abierta: los cupos libres de días pasados ya no se pueden usar y no cuentan.
- **Citas agendadas**, **espera media** y **desencuentros** cuentan todo lo sembrado desde el
  primer pedido (semana del demo).
- `semana` (opcional) acota a una semana Lun–Dom: los cupos a esa semana dentro de la agenda
  abierta, y las citas a las solicitadas en ella.
- Los umbrales de nivel salen de `coordinacion.nivel_ocupacion` en parametros.yaml.
"""

from collections import defaultdict
from datetime import date, timedelta

from ..repositories.app_state import AppState


def rango_semana(fecha: date) -> tuple[date, date]:
    """Lunes y domingo de la semana que contiene `fecha`."""
    lunes = fecha - timedelta(days=fecha.weekday())
    return lunes, lunes + timedelta(days=6)


def agenda(estado: AppState) -> tuple[date, date]:
    """Rango de toda la agenda generada."""
    return estado.escenario["agenda_desde"], estado.escenario["agenda_hasta"]


def agenda_abierta(estado: AppState) -> tuple[date, date]:
    """Rango que todavía se puede reservar: de hoy + 1 al fin de la agenda."""
    return estado.hoy + timedelta(days=1), estado.escenario["agenda_hasta"]


def rango_pedidos(estado: AppState) -> tuple[date, date]:
    """Rango en que se fecharon los pedidos sembrados: del lunes de la semana del demo a hoy."""
    return rango_semana(estado.hoy)[0], estado.hoy


def porcentaje(ocupados: int, liberados: int) -> float:
    return round(100 * ocupados / liberados, 1) if liberados else 0.0


def umbral_lote(estado: AppState) -> float:
    """Utilización (0–1) desde la cual un servicio entra en modo lote (`modo_lote_umbral_utilizacion`)."""
    return float(estado.parametros["modo_lote_umbral_utilizacion"])


def en_lote(estado: AppState, reservados: int, liberados: int) -> bool:
    """¿El servicio está en modo lote? Utilización = cupos reservados / cupos liberados de la agenda abierta."""
    return liberados > 0 and reservados / liberados >= umbral_lote(estado)


def nivel(estado: AppState, pct: float) -> str:
    """`baja` bajo el primer umbral, `alta` sobre el segundo y `media` en medio."""
    umbrales = estado.parametros["coordinacion"]["nivel_ocupacion"]
    if pct < umbrales["baja_menor_que"]:
        return "baja"
    return "alta" if pct > umbrales["alta_mayor_que"] else "media"


def rango_de_cupos(estado: AppState, semana: date | None) -> tuple[date, date]:
    """Agenda abierta, o su parte que cae en la semana pedida (vacía si no se cruzan)."""
    desde, hasta = agenda_abierta(estado)
    if semana is None:
        return desde, hasta
    inicio, fin = rango_semana(semana)
    return max(desde, inicio), min(hasta, fin)


def embudo_por_servicio(
    estado: AppState, semana: date | None = None
) -> tuple[date, date, dict[str, dict[str, int]]]:
    """Embudo de cupos por servicio sobre la agenda abierta (o la semana pedida).

    capacidad (cupos que el servicio atiende en el rango) → libres (tras la ocupación inicial)
    → liberados (la parte que presta a AURA) → reservados (ya asignados por AURA).
    """
    inicio, fin = rango_de_cupos(estado, semana)
    desde, hasta = inicio.isoformat(), fin.isoformat()
    por_servicio: dict[str, dict[str, int]] = defaultdict(
        lambda: {"capacidad": 0, "libres": 0, "liberados": 0, "reservados": 0}
    )
    for cupo in estado.motor.inventario_cupos():
        if desde <= cupo["fecha"] <= hasta:
            fila = por_servicio[cupo["service_id"]]
            fila["capacidad"] += 1
            fila["libres"] += not cupo["ocupado_inicial"]
            fila["liberados"] += cupo["liberado"]
            fila["reservados"] += cupo["reservado"]
    return inicio, fin, por_servicio


SIN_CUPOS = {"capacidad": 0, "libres": 0, "liberados": 0, "reservados": 0}


def suma_embudo(filas) -> dict[str, int]:
    """Suma de embudos (total de la red)."""
    total = dict(SIN_CUPOS)
    for fila in filas:
        for clave in total:
            total[clave] += fila[clave]
    return total
