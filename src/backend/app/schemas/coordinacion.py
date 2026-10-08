from datetime import date

from pydantic import BaseModel


class Kpis(BaseModel):
    citas_agendadas: int
    espera_media_dias: float
    espera_linea_base_dias: float
    capacidad_agenda_abierta: int  # capacidad prorrateada a los días de la agenda abierta
    libres_agenda_abierta: int  # después de la ocupación inicial
    cupos_liberados: int  # los que los servicios prestan a AURA
    cupos_reservados: int  # los que AURA ya asignó
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
    capacidad_semanal: int
    capacidad_agenda_abierta: int
    libres_agenda_abierta: int
    cupos_liberados: int
    cupos_reservados: int


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
    agenda_abierta: Rango  # rango del embudo de cupos y de la ocupación
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
    capacidad_semanal: int  # D6
    capacidad_agenda_abierta: int
    libres_agenda_abierta: int
    cupos_liberados: int
    cupos_reservados: int
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
    capacidad: int
    libres: int
    liberados: int
    reservados: int
    abierto: bool  # el día todavía se puede reservar (posterior a hoy)
