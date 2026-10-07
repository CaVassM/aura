from datetime import date

from pydantic import BaseModel

from .coordinacion import CuposDia, DemandaTipo, RecibidosAlternativa, ServicioProps


class Franja(BaseModel):
    dia: str
    desde: str
    hasta: str


class DesencuentroItem(BaseModel):
    id: str
    fecha: date
    motivo: str
    motivo_label: str
    servicio_ideal: str
    servicio_ideal_label: str
    distrito: str
    franja: Franja
    canales_aceptables: list[str]
    canales_label: list[str]
    grupo: str
    grupo_label: str


class Heatmap(BaseModel):
    dias: list[str]
    horas: list[int]
    celdas: list[list[int]]


class Insight(BaseModel):
    texto: str
    porcentaje: float
    grupo: str | None
    servicio_ideal: str | None
    franja: Franja | None


class DesencuentrosOut(BaseModel):
    total: int
    filtrados: int
    pagina: int
    paginas: int
    items: list[DesencuentroItem]
    heatmap: Heatmap
    insight: Insight


class ServicioDetalleOut(BaseModel):
    servicio: ServicioProps
    demanda_del_tipo: DemandaTipo
    recibidos_como_alternativa: RecibidosAlternativa
    cupos_por_dia: list[CuposDia]
    desencuentros_recientes: list[DesencuentroItem]
