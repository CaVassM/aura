"""Valida distribución de avisos y compara ansiedad solo de forma agregada."""

import csv
from datetime import date
from pathlib import Path

from aura.aviso.filtros import (
    _datos,
    _periodos,
    calcular_senales,
    estudiantes_para_aviso,
)
from aura.datos.carga import cargar_csv
from aura.herramientas.configuracion import RAIZ_PROYECTO, cargar_yaml, ruta_data_pack


def _fecha_evaluacion(periodo: str, d7: list[dict]) -> date:
    """Elige el primer día de evaluación disponible para cada periodo."""
    fechas = [
        date.fromisoformat(fila["start_date"])
        for fila in d7
        if fila["period_id"] == periodo and fila["event_type"] == "evaluation_week"
    ]
    if not fechas:
        raise ValueError(f"D7 no define semana de evaluación para {periodo}")
    return min(fechas)


def _porcentaje(numerador: int, denominador: int) -> float:
    """Devuelve porcentaje seguro cuando un periodo no tiene estudiantes."""
    return 100 * numerador / denominador if denominador else 0.0


def _medir_periodo(periodo, dia, d3, d7, parametros):
    """Resume elegibilidad y conteos de puntaje sin guardar identidad estudiantil."""
    umbrales = parametros["aviso"]
    periodos = _periodos(d7)
    indice = periodos.index(periodo)
    anterior = periodos[indice - 1] if indice else None
    filas = calcular_senales(periodo, d3, anterior, umbrales)
    conteos = {
        puntaje: sum(fila["puntaje"] == puntaje for fila in filas)
        for puntaje in range(5)
    }
    avisos = estudiantes_para_aviso(periodo, dia)
    return {
        "periodo": periodo,
        "fecha": dia.isoformat(),
        "estudiantes": len(filas),
        "elegibles": len(avisos),
        "porcentaje_elegible": _porcentaje(len(avisos), len(filas)),
        "puntaje_0": conteos[0],
        "puntaje_1": conteos[1],
        "puntaje_2": conteos[2],
        "puntaje_3": conteos[3],
        "puntaje_4": conteos[4],
        "filas_auditoria": filas,
    }


def _sensibilidad(periodo, d3, d7, parametros):
    """Mueve un umbral por vez y registra el porcentaje que supera el puntaje mínimo."""
    umbral_base = dict(parametros["aviso"])
    total = sum(fila["period_id"] == periodo for fila in d3)
    salidas = []
    pruebas = [
        ("caida_asistencia", [0.03, 0.05, 0.07]),
        ("cambio_nota", [-0.3, -0.5, -0.7]),
        ("puntaje_minimo", [1, 2, 3]),
    ]
    anteriores = _periodos(d7)
    idx = anteriores.index(periodo)
    periodo_anterior = anteriores[idx - 1] if idx else None
    for clave, valores in pruebas:
        for valor in valores:
            configuracion = {**umbral_base, clave: valor}
            filas = calcular_senales(periodo, d3, periodo_anterior, configuracion)
            cuenta = sum(
                fila["puntaje"] >= int(configuracion["puntaje_minimo"])
                for fila in filas
            )
            salidas.append(
                {
                    "periodo": periodo,
                    "umbral": clave,
                    "valor": valor,
                    "porcentaje_elegible": _porcentaje(cuenta, total),
                }
            )
    return salidas


def _validar_d1(periodo, senales, d1, minimo):
    """Compara medias de ansiedad por grupo agregado, sin exportar datos personales."""
    elegibles = {fila["estudiante_id"] for fila in senales if fila["puntaje"] >= minimo}
    ansiedad_elegibles = []
    ansiedad_no_elegibles = []
    ids_periodo = {fila["estudiante_id"] for fila in senales}
    for fila in d1:
        if fila["student_id"] not in ids_periodo:
            continue
        valor = float(fila["anxiety_score"])
        destino = (
            ansiedad_elegibles
            if fila["student_id"] in elegibles
            else ansiedad_no_elegibles
        )
        destino.append(valor)
    return {
        "periodo": periodo,
        "n_elegibles": len(ansiedad_elegibles),
        "ansiedad_media_elegibles": (
            sum(ansiedad_elegibles) / len(ansiedad_elegibles)
            if ansiedad_elegibles
            else None
        ),
        "n_no_elegibles": len(ansiedad_no_elegibles),
        "ansiedad_media_no_elegibles": (
            sum(ansiedad_no_elegibles) / len(ansiedad_no_elegibles)
            if ansiedad_no_elegibles
            else None
        ),
    }


def main() -> None:
    """Genera tablas de cobertura, sensibilidad y validación agregada con D1."""
    d3, d7 = _datos()
    parametros = cargar_yaml("parametros.yaml")
    periodos = _periodos(d7)
    periodos_validos = periodos[1:]
    d1 = cargar_csv(ruta_data_pack() / "D1_wellbeing_survey.csv")
    resumenes = []
    auditoria_agregada = []
    for periodo in periodos_validos:
        dia = _fecha_evaluacion(periodo, d7)
        resumen = _medir_periodo(periodo, dia, d3, d7, parametros)
        senales = resumen.pop("filas_auditoria")
        resumenes.append(resumen)
        auditoria_agregada.append(
            _validar_d1(
                periodo,
                senales,
                d1,
                int(parametros["aviso"]["puntaje_minimo"]),
            )
        )
    sensibilidad = _sensibilidad(periodos_validos[-1], d3, d7, parametros)
    salida = RAIZ_PROYECTO / "salidas"
    salida.mkdir(exist_ok=True)
    _guardar_csv(salida / "sensibilidad_aviso.csv", sensibilidad)
    _guardar_csv(salida / "validacion_aviso_d1_agregada.csv", auditoria_agregada)
    _guardar_reporte(
        salida / "validacion_aviso.md", resumenes, auditoria_agregada, sensibilidad
    )


def _guardar_csv(ruta: Path, filas: list[dict]) -> None:
    """Escribe resúmenes tabulares como UTF-8 sin BOM."""
    if not filas:
        return
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def _guardar_reporte(ruta: Path, resumenes, validacion, sensibilidad) -> None:
    """Escribe conclusiones agregadas y nunca incluye IDs ni ansiedad individual."""
    lineas = [
        "# Validación del aviso académico",
        "",
        "Los avisos solo se consideran durante semanas de evaluación según D7.",
        "",
        "## Cobertura y puntajes",
        "",
        "| Periodo | Fecha evaluada | Estudiantes | Elegibles | % elegible | Puntaje 0 | Puntaje 1 | Puntaje 2 | Puntaje 3 | Puntaje 4 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for fila in resumenes:
        lineas.append(
            f"| {fila['periodo']} | {fila['fecha']} | {fila['estudiantes']} | {fila['elegibles']} | "
            f"{fila['porcentaje_elegible']:.2f}% | {fila['puntaje_0']} | {fila['puntaje_1']} | "
            f"{fila['puntaje_2']} | {fila['puntaje_3']} | {fila['puntaje_4']} |"
        )
    lineas.extend(
        [
            "",
            "## Validación agregada con D1",
            "",
            "Se comparan promedios de anxiety_score solo para validar grupos; D1 no interviene en los filtros.",
            "",
            "| Periodo | n elegibles | Ansiedad media elegibles | n no elegibles | Ansiedad media no elegibles |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for fila in validacion:
        media_e = (
            "sin datos"
            if fila["ansiedad_media_elegibles"] is None
            else f"{fila['ansiedad_media_elegibles']:.2f}"
        )
        media_n = (
            "sin datos"
            if fila["ansiedad_media_no_elegibles"] is None
            else f"{fila['ansiedad_media_no_elegibles']:.2f}"
        )
        lineas.append(
            f"| {fila['periodo']} | {fila['n_elegibles']} | {media_e} | {fila['n_no_elegibles']} | {media_n} |"
        )
    lineas.extend(
        [
            "",
            "## Sensibilidad",
            "",
            "Cambios de un umbral por vez para el periodo más reciente.",
            "",
            "| Umbral | Valor | % elegible |",
            "|---|---:|---:|",
        ]
    )
    for fila in sensibilidad:
        lineas.append(
            f"| {fila['umbral']} | {fila['valor']} | {fila['porcentaje_elegible']:.2f}% |"
        )
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
