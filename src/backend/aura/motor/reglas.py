"""Compatibilidad, afinidad y precálculo de opciones válidas."""

from datetime import date, timedelta
from pathlib import Path
import yaml
from .datos import Cupo, Solicitud, Opcion

_RUTA_CONFIG = Path(__file__).resolve().parents[2] / "config" / "parametros.yaml"
_RUTA_TABLAS = Path(__file__).resolve().parents[2] / "config" / "tablas.yaml"
with _RUTA_CONFIG.open(encoding="utf-8") as _archivo:
    _PARAMETROS = yaml.safe_load(_archivo)
with _RUTA_TABLAS.open(encoding="utf-8") as _archivo:
    _TABLAS = yaml.safe_load(_archivo)
AFINIDAD = _TABLAS["afinidad"]
P_CANAL = _PARAMETROS["probabilidad_canal"]
UMBRAL_AFINIDAD = float(_PARAMETROS["umbral_afinidad"])
BETA_COSTO = float(_PARAMETROS["beta"])


def afinidad(ideal: str, tipo: str) -> float:
    """Devuelve la afinidad definida por el pedido (cero para pares desconocidos)."""
    return AFINIDAD.get(ideal, {}).get(tipo, 0.0)


def precalcular_opciones(
    solicitudes: list[Solicitud],
    cupos: list[Cupo],
    libres: set[str],
    hoy: date,
    beta: float = BETA_COSTO,
    horizonte_dias: int | None = None,
):
    """Evalúa R1-R6 una sola vez y regresa opciones por solicitud.

    `hoy` es la fecha de referencia. Si se indica `horizonte_dias`, la ventana de la solicitud
    es de hoy + 1 a hoy + horizonte_dias; si no, no hay cota superior.
    """
    por_solicitud = {}
    cupo_por_id = {c.id: c for c in cupos}
    for s in solicitudes:
        opciones = []
        for c in cupos:
            if c.id not in libres or c.fecha <= hoy:
                continue  # R5 y disponibilidad
            if horizonte_dias is not None and c.fecha > hoy + timedelta(days=horizonte_dias):
                continue  # fuera de la ventana de la solicitud
            if not any(
                f.dia_semana == c.fecha.weekday()
                and f.hora_inicio <= c.hora_inicio
                and c.hora_fin <= f.hora_fin
                for f in s.franjas
            ):
                continue  # R1
            a = afinidad(s.servicio_ideal, c.tipo)
            if a < UMBRAL_AFINIDAD:
                continue  # R2
            # Canales válidos del mismo cupo son alternativas dominadas salvo P:
            # el canal con mayor P siempre cuesta menos y consume el mismo cupo.
            canales_validos = [
                canal
                for canal in c.canales
                if canal in s.canales_aceptables
                and not (canal == "in_person" and c.distrito != s.distrito)
            ]
            if canales_validos:
                mejor_canal = max(
                    canales_validos, key=lambda canal: (P_CANAL[canal], canal)
                )
                opciones.append(Opcion(c.id, mejor_canal, a))
        # Ordenar una vez evita recalcular costos y buscar mínimos en cada individuo.
        por_solicitud[s.id] = tuple(
            sorted(
                opciones,
                key=lambda o: (
                    (cupo_por_id[o.cupo_id].fecha - hoy).days / P_CANAL[o.canal]
                    + beta * (1 - o.afinidad),
                    o.cupo_id,
                    o.canal,
                ),
            )
        )
    return por_solicitud


def vectorizar_opciones(opciones, cupos):
    """Prepara índices NumPy para consultar cupos libres en código vectorizado.

    Si NumPy no está instalado devuelve (None, None) y el decodificador usa
    el recorrido Python, que mantiene exactamente la misma lógica.
    """
    try:
        import numpy as np
    except ImportError:
        return None, None
    indice_cupo = {c.id: i for i, c in enumerate(cupos)}
    indices = {
        sid: np.asarray([indice_cupo[o.cupo_id] for o in lista], dtype=np.int32)
        for sid, lista in opciones.items()
    }
    return indices, indice_cupo
