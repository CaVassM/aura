"""Señales agregadas de trayectoria; D1 queda fuera de la decisión de elegibilidad."""

import csv
from datetime import date
from functools import lru_cache
from pathlib import Path

from ..datos.carga import cargar_data_pack
from ..herramientas.configuracion import RAIZ_PROYECTO, cargar_yaml, ruta_data_pack


@lru_cache(maxsize=1)
def _datos() -> tuple[list[dict], list[dict]]:
    """Carga D3 y D7 una vez; D1 no participa en este flujo."""
    datos = cargar_data_pack(ruta_data_pack())
    return datos["d3"], datos["d7"]


def _periodos(d7: list[dict]) -> list[str]:
    """Ordena periodos cronológicamente usando sus marcas de inicio en D7."""
    inicios = {}
    for fila in d7:
        if fila["event_type"] == "period_start":
            inicios[fila["period_id"]] = fila["start_date"]
    return sorted(inicios, key=lambda periodo: inicios[periodo])


def _es_semana_evaluacion(periodo: str, dia: date, d7: list[dict], evento: str) -> bool:
    """Comprueba que la fecha esté dentro de una evaluación del periodo indicado."""
    for fila in d7:
        if fila["period_id"] != periodo or fila["event_type"] != evento:
            continue
        desde = date.fromisoformat(fila["start_date"])
        hasta = date.fromisoformat(fila.get("end_date") or fila["start_date"])
        if desde <= dia <= hasta:
            return True
    return False


def _percentil(valores: list[float], q: float) -> float:
    """Calcula el percentil lineal para identificar cargas altas sin dependencia externa."""
    ordenados = sorted(valores)
    if not ordenados:
        return float("inf")
    posicion = (len(ordenados) - 1) * q
    inferior = int(posicion)
    superior = min(inferior + 1, len(ordenados) - 1)
    fraccion = posicion - inferior
    return ordenados[inferior] * (1 - fraccion) + ordenados[superior] * fraccion


def calcular_senales(
    periodo: str,
    d3: list[dict],
    periodo_anterior: str | None,
    umbrales: dict,
) -> list[dict]:
    """Compara dos periodos y conserva las cuatro señales solo para auditoría."""
    actuales = {fila["student_id"]: fila for fila in d3 if fila["period_id"] == periodo}
    anteriores = {
        fila["student_id"]: fila
        for fila in d3
        if periodo_anterior and fila["period_id"] == periodo_anterior
    }
    cargas = [float(fila["credit_load"]) for fila in actuales.values()]
    corte_carga = _percentil(cargas, float(umbrales["percentil_carga_creditos"]))
    filas = []
    for estudiante_id, actual in actuales.items():
        previo = anteriores.get(estudiante_id)
        s1 = actual["dropout_alert"].lower() in umbrales["dropout_alert"]
        s2 = bool(previo) and float(previo["attendance_rate"]) - float(
            actual["attendance_rate"]
        ) >= float(umbrales["caida_asistencia"])
        s3 = float(actual["grade_change"]) <= float(umbrales["cambio_nota"])
        s4 = float(actual["credit_load"]) >= corte_carga
        senales = {
            "S1_dropout": int(s1),
            "S2_asistencia": int(s2),
            "S3_cambio_nota": int(s3),
            "S4_carga_creditos": int(s4),
        }
        filas.append(
            {
                "estudiante_id": estudiante_id,
                "puntaje": sum(senales.values()),
                **senales,
            }
        )
    return filas


def _guardar_auditoria(periodo: str, dia: date, filas: list[dict]) -> None:
    """Guarda señales estudiante a estudiante en un archivo separado de avisos."""
    ruta = RAIZ_PROYECTO / "salidas" / "aviso_auditoria.csv"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    campos = [
        "periodo",
        "fecha",
        "estudiante_id",
        "puntaje",
        "S1_dropout",
        "S2_asistencia",
        "S3_cambio_nota",
        "S4_carga_creditos",
    ]
    previas = []
    if ruta.exists():
        with ruta.open("r", encoding="utf-8", newline="") as archivo:
            previas = [
                fila for fila in csv.DictReader(archivo)
                if fila["periodo"] != periodo or fila["fecha"] != dia.isoformat()
            ]
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(previas)
        for fila in filas:
            escritor.writerow({"periodo": periodo, "fecha": dia.isoformat(), **fila})


def estudiantes_para_aviso(
    periodo: str, fecha: date | str
) -> list[dict[str, int | str]]:
    """Entrega solo estudiante y puntaje durante semanas de evaluación de D7."""
    dia = date.fromisoformat(fecha) if isinstance(fecha, str) else fecha
    d3, d7 = _datos()
    parametros = cargar_yaml("parametros.yaml")["aviso"]
    if not _es_semana_evaluacion(periodo, dia, d7, parametros["evento_evaluacion"]):
        return []
    periodos = _periodos(d7)
    indice = periodos.index(periodo) if periodo in periodos else -1
    anterior = periodos[indice - 1] if indice > 0 else None
    senales = calcular_senales(periodo, d3, anterior, parametros)
    _guardar_auditoria(periodo, dia, senales)
    minimo = int(parametros["puntaje_minimo"])
    return [
        {"estudiante_id": fila["estudiante_id"], "puntaje": fila["puntaje"]}
        for fila in senales
        if fila["puntaje"] >= minimo
    ]
