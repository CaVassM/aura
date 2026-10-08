"""Resumen por consola de la siembra: `python -m app.cli_siembra x1 x4.3`."""

import sys
from collections import Counter

from .services.resumen_service import ResumenService
from .services.siembra_service import crear_estado_sembrado
from .settings import Settings


def resumen(estado) -> dict:
    datos = ResumenService(estado).resumen()
    return {
        "escenario": estado.escenario["etiqueta"],
        "siembra": estado.siembra,
        "kpis": datos["kpis"],
        "des_por_grupo": dict(Counter(d["grupo"] for d in estado.desencuentros)),
        "por_servicio": {
            s["nombre"]: (s["cupos_reservados"], s["cupos_liberados"]) for s in datos["servicios"]
        },
    }


def main(nombres: list[str]) -> None:
    settings = Settings.desde_entorno()
    filas = [resumen(crear_estado_sembrado(settings, nombre)) for nombre in nombres]
    for nombre, f in zip(nombres, filas):
        k = f["kpis"]
        print(f"\n=== {nombre} · {f['escenario']}")
        print(f"  solicitudes: {f['siembra']}")
        print(
            f"  citas {k['citas_agendadas']} · espera media {k['espera_media_dias']} d "
            f"(línea base {k['espera_linea_base_dias']} d)"
        )
        print(f"  ocupación de la semana {k['ocupacion_pct']} % de {k['cupos_liberados']} liberados")
        print(f"  desencuentros {k['desencuentros']} · por grupo {f['des_por_grupo']}")
    print("\nOcupación semanal por servicio (reservados/liberados · %):")
    for servicio in filas[0]["por_servicio"]:
        celdas = []
        for f in filas:
            o, lib = f["por_servicio"][servicio]
            celdas.append(f"{o:>3}/{lib:<3} {100 * o / lib if lib else 0:5.1f}%")
        print(f"  {servicio:<30} " + "   |   ".join(celdas))


if __name__ == "__main__":
    main(sys.argv[1:] or ["x1", "x4.3"])
