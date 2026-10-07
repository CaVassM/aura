"""Generación determinista y configurable de la oferta de cupos."""

from datetime import date, datetime, time, timedelta
import random
from .datos import Servicio, Cupo


def _bloques_de_semana(
    primer_dia: date, semanas: int, ultimo_dia: date | None, calendario: bool
) -> list[tuple[date, date]]:
    """Tramos (primer día, último día) en los que se reparte la capacidad semanal.

    Por defecto, `semanas` tramos de 7 días desde `primer_dia`. En modo calendario, las semanas
    Lun–Dom que cruzan el rango [`primer_dia`, `ultimo_dia`], recortadas por sus extremos.
    """
    if not calendario:
        return [
            (
                primer_dia + timedelta(days=7 * n),
                primer_dia + timedelta(days=7 * n + 6),
            )
            for n in range(semanas)
        ]
    tramos = []
    lunes = primer_dia - timedelta(days=primer_dia.weekday())
    while lunes <= ultimo_dia:
        tramos.append((max(lunes, primer_dia), min(lunes + timedelta(days=6), ultimo_dia)))
        lunes += timedelta(days=7)
    return tramos


def _capacidad_del_tramo(servicio: Servicio, inicio: date, fin: date, calendario: bool) -> int:
    """Capacidad semanal completa, o proporcional a los días de atención dentro del tramo."""
    if not calendario:
        return servicio.capacidad_semanal
    dias_atencion = {dia for dia, _, _ in servicio.dias_horas}
    dentro = sum(
        1
        for n in range((fin - inicio).days + 1)
        if (inicio + timedelta(days=n)).weekday() in dias_atencion
    )
    return round(servicio.capacidad_semanal * dentro / len(dias_atencion))


def generar_agenda(
    servicios: list[Servicio],
    hoy: date,
    semanas: int = 2,
    duracion_min: int = 60,
    fraccion_liberada: float = 0.5,
    ocupacion_inicial: float | dict[str, float] = 0.10,
    semilla: int = 42,
    dias_cerrados: set[date] | None = None,
    primer_dia: date | None = None,
    ultimo_dia: date | None = None,
    semana_calendario: bool = False,
) -> tuple[list[Cupo], set[str]]:
    """Crea slots, marca ocupación previa y libera una fracción de los restantes.

    Por defecto la agenda empieza el día siguiente a `hoy` y cada bloque de 7 días desde ahí
    recibe la capacidad semanal del servicio. `primer_dia` y `ultimo_dia` (inclusive) fijan el
    rango. Con `semana_calendario` la capacidad se reparte por semana Lun–Dom; una semana
    cortada por el inicio o el fin del rango recibe capacidad proporcional a los días de
    atención que caen dentro (en ese modo `semanas` no se usa: el rango lo define).

    La capacidad se reparte equitativamente entre bloques horarios de cada semana;
    cualquier resto se asigna, de a uno, a los primeros bloques.
    """
    if duracion_min <= 0 or semanas <= 0 or not 0 <= fraccion_liberada <= 1:
        raise ValueError(
            "Duración/semanas deben ser positivas y fracción estar entre 0 y 1"
        )
    if semana_calendario and ultimo_dia is None:
        raise ValueError("semana_calendario requiere ultimo_dia")
    rng = random.Random(semilla)
    cerrados = dias_cerrados or set()
    cupos: list[Cupo] = []
    libres: set[str] = set()
    numero = 0
    primer_dia = primer_dia or hoy + timedelta(days=1)
    for inicio_bloque, fin_bloque in _bloques_de_semana(
        primer_dia, semanas, ultimo_dia, semana_calendario
    ):
        for servicio in servicios:
            bloques: list[tuple[date, time, time]] = []
            for desplazamiento in range(7):
                fecha = inicio_bloque + timedelta(days=desplazamiento)
                if fecha in cerrados or (ultimo_dia is not None and fecha > ultimo_dia):
                    continue
                if semana_calendario and fecha > fin_bloque:
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
            capacidad = _capacidad_del_tramo(
                servicio, inicio_bloque, fin_bloque, semana_calendario
            )
            q, r = divmod(capacidad, len(bloques))
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
