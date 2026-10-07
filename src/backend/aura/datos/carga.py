"""Carga de datos AURA; centraliza formatos y evita modificar los archivos fuente."""

from pathlib import Path

from .modelos import cargar_csv, cargar_servicios, cierres_desde_d7


def cargar_data_pack(ruta: Path) -> dict[str, object]:
    """Lee D1, D2, D3, D6 y D7 desde una ruta configurable del Data Pack."""
    return {
        "d1": cargar_csv(ruta / "D1_wellbeing_survey.csv"),
        "d2": cargar_csv(ruta / "D2_support_services.csv"),
        "d3": cargar_csv(ruta / "D3_academic_trajectory.csv"),
        "servicios": cargar_servicios(ruta / "D6_services_map.geojson"),
        "d7": cargar_csv(ruta / "D7_calendar.csv"),
    }
