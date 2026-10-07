from datetime import date

from pydantic import BaseModel


class Kpis(BaseModel):
    citas_agendadas: int
    espera_media_dias: float
    espera_linea_base_dias: float
    cupos_liberados: int
    cupos_ocupados: int
    ocupacion_pct: float
    desencuentros: int
    atendidos_alternativa: int  # pedidos atendidos en un tipo distinto del ideal (por afinidad)


class ServicioResumen(BaseModel):
    service_id: str
    nombre: str
    tipo: str
    tipo_label: str
    ocupacion_pct: float
    nivel: str
    cupos_liberados: int
    cupos_ocupados: int


class Rango(BaseModel):
    desde: date
    hasta: date


class Destino(BaseModel):
    tipo: str
    tipo_label: str
    cantidad: int


class DemandaTipo(BaseModel):
    ideal: str
    ideal_label: str
    pedidos: int  # atendidos (en su tipo o con alternativa) + sin cupo
    atendidos_en_su_tipo: int
    atendidos_con_alternativa: int
    sin_cupo: int  # desencuentros
    destinos: list[Destino]  # a qué tipo se desvió la demanda


class RecibidosAlternativa(BaseModel):
    cantidad: int  # citas de este servicio cuyo pedido pedía otro tipo
    origenes: list[Destino]


class ResumenOut(BaseModel):
    agenda_abierta: Rango  # rango de cupos liberados / ocupados / ocupación
    pedidos: Rango  # rango de pedidos que cuentan las citas y la espera
    kpis: Kpis
    demanda_por_tipo: list[DemandaTipo]
    servicios: list[ServicioResumen]


class Pos(BaseModel):
    x: float
    y: float


class HorarioTramo(BaseModel):
    dias: list[str]
    desde: str
    hasta: str


class ServicioProps(BaseModel):
    service_id: str
    nombre: str
    tipo: str
    tipo_label: str
    distrito: str
    direccion: str | None
    horario_texto: str
    horario: list[HorarioTramo]
    canales: list[str]
    canales_label: list[str]
    capacidad_semanal: int
    cupos_liberados: int
    cupos_ocupados: int
    ocupacion_pct: float
    nivel: str
    alta_demanda: bool
    eligibility: str | None
    referral_information: str | None
    pos: Pos


class ServicioFeature(BaseModel):
    type: str = "Feature"
    id: str
    geometry: dict
    properties: ServicioProps


class ServiciosGeoJSON(BaseModel):
    type: str = "FeatureCollection"
    features: list[ServicioFeature]


class CuposDia(BaseModel):
    fecha: date
    dia: str
    liberados: int
    ocupados: int
    abierto: bool  # el día todavía se puede reservar (posterior a hoy)
