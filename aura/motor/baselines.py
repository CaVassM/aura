"""Baselines, normalización multiobjetivo y lote de demostración."""

from datetime import date, time, timedelta
from collections import Counter
from pathlib import Path
import yaml
from .datos import Solicitud, Franja
from .reglas import precalcular_opciones
from .genetico import genetico

_RUTA_CONFIG = Path(__file__).resolve().parents[2] / "config"
with (_RUTA_CONFIG / "parametros.yaml").open(encoding="utf-8") as _archivo:
    PESOS = yaml.safe_load(_archivo)["pesos_z"]
with (_RUTA_CONFIG / "tablas.yaml").open(encoding="utf-8") as _archivo:
    MAPA_MOTIVOS = yaml.safe_load(_archivo)["motivo_a_servicio"]


def orden_llegada(solicitudes):
    """Orden estable por fecha de solicitud e ID para empates."""
    return [s.id for s in sorted(solicitudes, key=lambda s: (s.fecha_solicitud, s.id))]


def normalizar_pagos(matrices):
    """Zmin diagonal y Zmax por columna a partir de cinco corridas monoobjetivo."""
    claves = list(PESOS)
    zmin = {k: min(fila[k] for fila in matrices) for k in claves}
    zmax = {k: max(fila[k] for fila in matrices) for k in claves}
    return zmin, zmax


def z_normalizado(metricas, zmin, zmax, pesos=PESOS):
    """Suma ponderada de términos normalizados y protege denominadores nulos."""
    return sum(
        pesos[k]
        * ((metricas[k] - zmin[k]) / (zmax[k] - zmin[k]) if zmax[k] != zmin[k] else 0.0)
        for k in pesos
    )


def z_plan_b(metricas, n, dias_horizonte):
    """Referencias fijas transparentes si no se calibra la tabla de pagos."""
    refs = {
        "Z1": max(1, n),
        "Z2": max(1, n * dias_horizonte / 0.667),
        "Z3": 1.0,
        "Z4": max(1, dias_horizonte),
        "Z5": max(1, n),
    }
    return sum(PESOS[k] * min(1.0, metricas[k] / refs[k]) for k in PESOS)


def simular_solicitudes(d2, d1, fecha_base, semilla=42):
    """Toma una semana mediana de D2 y documenta preferencias heurísticas del demo."""
    import random

    rng = random.Random(semilla)
    por_fecha = Counter(r["request_date"] for r in d2)
    semanas = Counter()
    for f, n in por_fecha.items():
        dt = date.fromisoformat(f)
        lunes = date.fromordinal(dt.toordinal() - dt.weekday())
        semanas[lunes] += n
    semana = min(
        semanas,
        key=lambda x: (
            abs(semanas[x] - sorted(semanas.values())[len(semanas) // 2]),
            x,
        ),
    )
    filas = [
        r
        for r in d2
        if semana
        <= date.fromisoformat(r["request_date"])
        < semana.fromordinal(semana.toordinal() + 7)
    ]
    perfiles = {r["student_id"]: r for r in d1}
    solic = []
    prop_tarde = sum(r.get("study_mode") == "evening" for r in d1) / max(1, len(d1))
    prob_extra = max(0.0, (0.16 - prop_tarde) / max(1e-9, 1 - prop_tarde))
    for i, r in enumerate(filas):
        motivo = r["reason_code"]
        ideal = MAPA_MOTIVOS.get(
            motivo, "counseling"
        )  # preventivo usa counseling por decisión conservadora
        perfil = perfiles.get(r["student_id"])
        # Conserva evening de D1 y completa probabilísticamente hasta ~16% total.
        # Si no hay perfil, se aplica directamente la tasa objetivo del 16%.
        nocturno = (
            (perfil.get("study_mode") == "evening") if perfil else (rng.random() < 0.16)
        )
        if perfil and not nocturno:
            nocturno = rng.random() < prob_extra
        grupo = "nocturno" if nocturno else "diurno"
        if nocturno and (
            (perfil or {}).get("employment_status") in {"part_time", "full_time"}
        ):
            franjas = tuple(Franja(d, time(19), time(21)) for d in range(5))
        elif nocturno:
            franjas = tuple(Franja(d, time(17), time(21)) for d in range(5))
        else:
            franjas = tuple(Franja(d, time(9), time(18)) for d in range(5))
        distrito = (perfil or {}).get("district_id") or rng.choice(
            ["DIST_GAIA", "DIST_NEBULA", "DIST_VECTOR", "DIST_HORIZON", "DIST_QUANTUM"]
        )
        canales = tuple(
            rng.choice(
                [
                    ("digital", "in_person"),
                    ("digital", "phone"),
                    ("digital", "phone", "in_person"),
                ]
            )
        )
        # Conservamos el día relativo de llegada, pero lo movemos a la semana anterior
        # al día base para que el baseline tenga un orden cronológico realista.
        lunes_base = fecha_base - timedelta(days=fecha_base.weekday() + 7)
        llegada = lunes_base + timedelta(
            days=date.fromisoformat(r["request_date"]).weekday()
        )
        solic.append(
            Solicitud(
                f"DEMO_{i+1:04d}", ideal, distrito, franjas, canales, llegada, grupo
            )
        )
    return solic, {
        "semana_origen": str(semana),
        "n_semana": len(solic),
        "motivos_desconocidos": sorted(
            set(r["reason_code"] for r in filas)
            - set(MAPA_MOTIVOS)
            - {"preventive_guidance"}
        ),
    }


def escalar_demanda(solicitudes, factor, semilla=42):
    """Replica solicitudes de forma reproducible para los escenarios de carga."""
    import random

    rng = random.Random(semilla)
    salida = []
    for copia in range(int(factor)):
        for s in solicitudes:
            salida.append(
                Solicitud(
                    f"{s.id}_x{copia+1}",
                    s.servicio_ideal,
                    s.distrito,
                    s.franjas,
                    s.canales_aceptables,
                    s.fecha_solicitud,
                    s.grupo,
                )
            )
    resto = round((factor - int(factor)) * len(solicitudes))
    for s in rng.sample(solicitudes, min(resto, len(solicitudes))):
        salida.append(
            Solicitud(
                f"{s.id}_extra{factor}",
                s.servicio_ideal,
                s.distrito,
                s.franjas,
                s.canales_aceptables,
                s.fecha_solicitud,
                s.grupo,
            )
        )
    return salida
