"""Generación determinista y configurable de la oferta de cupos."""

from datetime import date, datetime, time, timedelta
import random
from .datos import Servicio, Cupo


def generar_agenda(
    servicios: list[Servicio],
    hoy: date,
    semanas: int = 2,
    duracion_min: int = 60,
    fraccion_liberada: float = 0.5,
    ocupacion_inicial: float | dict[str, float] = 0.10,
    semilla: int = 42,
    dias_cerrados: set[date] | None = None,
) -> tuple[list[Cupo], set[str]]:
    """Crea slots, marca ocupación previa y libera una fracción de los restantes.

    La capacidad se reparte equitativamente entre bloques horarios de cada semana;
    cualquier resto se asigna, de a uno, a los primeros bloques.
    """
    if duracion_min <= 0 or semanas <= 0 or not 0 <= fraccion_liberada <= 1:
        raise ValueError(
            "Duración/semanas deben ser positivas y fracción estar entre 0 y 1"
        )
    rng = random.Random(semilla)
    cerrados = dias_cerrados or set()
    cupos: list[Cupo] = []
    libres: set[str] = set()
    numero = 0
    for semana in range(semanas):
        inicio = hoy + timedelta(days=1 + 7 * semana)
        for servicio in servicios:
            bloques: list[tuple[date, time, time]] = []
            for desplazamiento in range(7):
                fecha = inicio + timedelta(days=desplazamiento)
                if fecha in cerrados:
                    continue
                for dia, desde, hasta in servicio.dias_horas:
                    if fecha.weekday() != dia:
                        continue
                    actual = datetime.combine(fecha, desde)
                    limite = datetime.combine(fecha, hasta)
                    while actual + timedelta(minutes=duracion_min) <= limite:
                        fin = actual + timedelta(minutes=duracion_min)
                        bloques.append((fecha, actual.time(), fin.time()))
                        actual = fin
            if not bloques:
                continue
            q, r = divmod(servicio.capacidad_semanal, len(bloques))
            ids_semana = []
            for i, bloque in enumerate(bloques):
                for _ in range(q + (i < r)):
                    numero += 1
                    cid = f"C{numero:07d}"
                    cupos.append(
                        Cupo(
                            cid,
                            servicio.service_id,
                            servicio.tipo,
                            servicio.distrito,
                            *bloque,
                            servicio.canales,
                        )
                    )
                    ids_semana.append(cid)
            rng.shuffle(ids_semana)
            fraccion_ocupada = (
                ocupacion_inicial.get(servicio.service_id, 0.10)
                if isinstance(ocupacion_inicial, dict)
                else ocupacion_inicial
            )
            n_ocupados = min(len(ids_semana), round(len(ids_semana) * fraccion_ocupada))
            ocupados = set(ids_semana[:n_ocupados])
            restantes = ids_semana[n_ocupados:]
            liberados = round(len(restantes) * fraccion_liberada)
            libres.update(restantes[:liberados])
    return cupos, libres
