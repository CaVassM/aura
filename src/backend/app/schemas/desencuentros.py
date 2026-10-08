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


class ServicioColumna(BaseModel):
    tipo: str
    label: str


class MatrizDistritoServicio(BaseModel):
    """Conteo de desencuentros: filas = distritos, columnas = servicio ideal (respeta los filtros)."""

    distritos: list[str]
    servicios: list[ServicioColumna]
    celdas: list[list[int]]
    total_filas: list[int]
    total_columnas: list[int]
    total: int


class FranjaPrincipal(BaseModel):
    texto: str  # p. ej. "entre 19:00 y 21:00, lunes a viernes"
    porcentaje: float  # % de los pedidos del conjunto filtrado que declaran esa franja
    desde: str
    hasta: str
    dias: str


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
    matriz_distrito_servicio: MatrizDistritoServicio
    franja_principal: FranjaPrincipal | None
    insight: Insight  # sobre todos los desencuentros, sin filtros
    insight_filtro: Insight | None  # sobre el conjunto filtrado; None si no hay filtros activos


class ServicioDetalleOut(BaseModel):
    servicio: ServicioProps
    demanda_del_tipo: DemandaTipo
    recibidos_como_alternativa: RecibidosAlternativa
    cupos_por_dia: list[CuposDia]
    desencuentros_recientes: list[DesencuentroItem]
