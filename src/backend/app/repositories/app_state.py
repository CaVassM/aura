"""Estado único en RAM de la plataforma (singleton por proceso).

Lo comparten la vista de Coordinación y la del estudiante: cualquier reserva o
desencuentro se ve en ambas sin reiniciar. Las escrituras se hacen bajo `lock`.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from threading import RLock

from aura.herramientas.configuracion import cargar_yaml
from aura.servicio import ServicioAsignacion

from ..settings import Settings
from .cita_repository import CitaRepository
from .geo_d6 import cargar_geo_d6


@dataclass
class AppState:
    settings: Settings
    parametros: dict
    tablas: dict
    escenario: dict  # nombre, factor, fraccion_liberada, semilla, hoy, agenda_desde/hasta, …
    motor: ServicioAsignacion  # agenda, citas vivas y desencuentros del motor
    geo: list[dict]  # features de D6 con pos
    espera_linea_base_dias: float
    citas: CitaRepository = field(default_factory=CitaRepository)
    siembra: dict = field(default_factory=dict)
    lock: RLock = field(default_factory=RLock)

    @property
    def desencuentros(self) -> list[dict]:
        """Desencuentros registrados (los guarda el motor; una sola fuente)."""
        return self.motor.desencuentros()

    @property
    def hoy(self) -> date:
        return self.escenario["hoy"]

    def reemplazar_por(self, otro: "AppState") -> None:
        """Reemplaza el contenido conservando este objeto y su lock (reinicio de la demo)."""
        with self.lock:
            for nombre, valor in vars(otro).items():
                if nombre != "lock":
                    setattr(self, nombre, valor)


def construir_estado(
    settings: Settings, escenario: str | None = None, semilla: int | None = None
) -> AppState:
    """Carga YAML y D6, arma la agenda del escenario (sin sembrar demanda)."""
    parametros = cargar_yaml("parametros.yaml")
    tablas = cargar_yaml("tablas.yaml")
    demo = parametros["demo"]
    nombre = escenario or demo["escenario"]
    config = next(
        (e for e in parametros["experimento"]["escenarios"] if e["nombre"] == nombre),
        None,
    )
    if config is None:
        raise ValueError(f"Escenario desconocido en parametros.yaml: {nombre}")
    factor = float(config["factor"])
    hoy = date.fromisoformat(demo["hoy"])
    # La agenda abre el día siguiente al primer pedido (lunes de la semana de `hoy`) y llega
    # hasta hoy + horizonte.
    agenda_desde = hoy - timedelta(days=hoy.weekday()) + timedelta(days=1)
    agenda_hasta = hoy + timedelta(days=7 * int(parametros["horizonte_semanas"]))
    motor = ServicioAsignacion(
        data_pack=settings.data_dir,
        hoy=hoy,
        fraccion_liberada=float(config["fraccion_liberada"]),
        desde=agenda_desde,
        hasta=agenda_hasta,
        semana_calendario=True,  # D6 reparte la capacidad por semana Lun–Dom
    )
    proporcion = float(demo["proporcion_vespertino_trabaja"])
    plantilla = demo.get("etiquetas_por_escenario", {}).get(nombre, demo["etiqueta_escenario"])
    etiqueta = plantilla.format(factor=f"{factor:g}".replace(".", ","))
    if proporcion > 0:
        pct = f"{100 * proporcion:g}".replace(".", ",")
        etiqueta += demo["etiqueta_vespertino"].format(pct=pct)
    historica = motor.espera_historica_dias()
    return AppState(
        settings=settings,
        parametros=parametros,
        tablas=tablas,
        escenario={
            "nombre": nombre,
            "factor": factor,
            "fraccion_liberada": float(config["fraccion_liberada"]),
            "semilla": int(semilla if semilla is not None else demo["semilla"]),
            "hoy": hoy,
            "agenda_desde": agenda_desde,
            "agenda_hasta": agenda_hasta,
            "proporcion_vespertino_trabaja": proporcion,
            "etiqueta": etiqueta,
        },
        motor=motor,
        geo=cargar_geo_d6(settings.data_dir / "D6_services_map.geojson"),
        espera_linea_base_dias=(
            historica if historica is not None else float(demo["espera_linea_base_dias"])
        ),
    )
