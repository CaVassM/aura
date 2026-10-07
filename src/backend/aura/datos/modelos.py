"""Modelos y lectura de datos del Data Pack (solo lectura)."""

from dataclasses import dataclass
from datetime import date, time, timedelta
from pathlib import Path
import csv, json, re

DIAS = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6}


@dataclass(frozen=True)
class Servicio:
    """Servicio semanal y horario interpretado desde D6."""

    service_id: str
    tipo: str
    distrito: str
    dias_horas: tuple[tuple[int, time, time], ...]
    capacidad_semanal: int
    canales: tuple[str, ...]
    nombre: str = ""


@dataclass(frozen=True)
class Cupo:
    """Un espacio de una sesión en una fecha y canal potencial."""

    id: str
    service_id: str
    tipo: str
    distrito: str
    fecha: date
    hora_inicio: time
    hora_fin: time
    canales: tuple[str, ...]


@dataclass(frozen=True)
class Franja:
    """Día de semana y límites horarios aceptables por una solicitud."""

    dia_semana: int
    hora_inicio: time
    hora_fin: time


@dataclass(frozen=True)
class Solicitud:
    """Necesidad de cita y preferencias declaradas o simuladas."""

    id: str
    servicio_ideal: str
    distrito: str
    franjas: tuple[Franja, ...]
    canales_aceptables: tuple[str, ...]
    fecha_solicitud: date
    grupo: str
    motivo: str = ""


@dataclass(frozen=True)
class Opcion:
    """Par válido (cupo, canal), junto con su afinidad calculada."""

    cupo_id: str
    canal: str
    afinidad: float


def parsear_horario(schedule: str) -> tuple[tuple[int, time, time], ...]:
    """Convierte expresiones como Mon-Fri 09:00-18:00 en días y horas."""
    dias_txt, horas_txt = schedule.split()
    ini, fin = (time.fromisoformat(x) for x in horas_txt.split("-"))
    resultado = []
    for tramo in dias_txt.split(","):
        extremos = tramo.split("-")
        if len(extremos) == 1:
            resultado.append((DIAS[extremos[0]], ini, fin))
        else:
            a, b = map(lambda x: DIAS[x], extremos)
            resultado.extend((d, ini, fin) for d in range(a, b + 1))
    return tuple(resultado)


def cargar_servicios(ruta: Path) -> list[Servicio]:
    """Lee el GeoJSON y transforma sus propiedades sin escribir sobre el origen."""
    data = json.loads(ruta.read_text(encoding="utf-8"))
    return [
        Servicio(
            p["service_id"],
            p["service_type"],
            p["district_id"],
            parsear_horario(p["schedule"]),
            int(p["capacity"]),
            tuple(p["channels"]),
            p.get("name", ""),
        )
        for f in data["features"]
        if (p := f["properties"])
    ]


def cargar_csv(ruta: Path) -> list[dict[str, str]]:
    """Lee CSV con UTF-8 y devuelve filas como diccionarios."""
    with ruta.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def cierres_desde_d7(filas: list[dict[str, str]]) -> set[date]:
    """Interpreta explícitamente como cierre eventos marcados holiday/closed.

    Actividades universitarias y semanas de evaluación no se consideran cierres
    si D7 no indica que el servicio suspenda atención.
    """
    tipos_cierre = {
        "holiday",
        "feriado",
        "closure",
        "closed",
        "service_closed",
        "cierre_servicio",
    }
    cerrados = set()
    for fila in filas:
        if fila.get("event_type", "").strip().lower() not in tipos_cierre:
            continue
        desde = date.fromisoformat(fila["start_date"])
        hasta = date.fromisoformat(fila.get("end_date") or fila["start_date"])
        while desde <= hasta:
            cerrados.add(desde)
            desde += timedelta(days=1)
    return cerrados
