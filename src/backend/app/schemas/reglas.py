from pydantic import BaseModel


class MotivoServicio(BaseModel):
    motivo: str
    motivo_label: str
    servicio: str
    servicio_label: str


class MotivoServicioBloque(BaseModel):
    provisional: bool
    items: list[MotivoServicio]


class TipoServicio(BaseModel):
    codigo: str
    label: str


class AfinidadValor(BaseModel):
    tipo: str
    tipo_label: str
    valor: float


class AfinidadFila(BaseModel):
    ideal: str
    ideal_label: str
    valores: list[AfinidadValor]


class AfinidadBloque(BaseModel):
    provisional: bool
    minimo_alternativa: float
    minimo_provisional: bool
    tipos: list[TipoServicio]
    matriz: list[AfinidadFila]


class Senal(BaseModel):
    id: str
    nombre: str
    descripcion: str
    umbral: float | str | list[str]  # valor tal como está en la configuración
    umbral_texto: str  # el mismo valor en español, para mostrar


class AvisoBloque(BaseModel):
    provisional: bool
    puntaje_minimo: int
    total_senales: int
    regla: str  # «En semana de evaluaciones (D7), el aviso aparece con al menos 2 de estas 3 señales: …»
    solo_semanas_evaluacion: bool
    evento_evaluacion: str | None
    senales: list[Senal]


class AsistenciaCanal(BaseModel):
    canal: str
    canal_label: str
    valor: float


class AsistenciaBloque(BaseModel):
    provisional: bool
    canales: list[AsistenciaCanal]


class Termino(BaseModel):
    id: str
    nombre: str
    peso: float


class PesosBloque(BaseModel):
    provisional: bool
    terminos: list[Termino]


class EquidadBloque(BaseModel):
    provisional: bool
    max_citas_activas_por_tipo: int  # R7


class ModoLoteBloque(BaseModel):
    provisional: bool
    umbral_pct: float  # utilización desde la cual un servicio entra en modo lote (= nivel «alta»)
    ventana_s: int
    tamano_maximo: int
    max_opciones: int


class ReglasOut(BaseModel):
    motivo_servicio: MotivoServicioBloque
    afinidad: AfinidadBloque
    aviso: AvisoBloque
    p_asistencia: AsistenciaBloque
    pesos: PesosBloque
    equidad: EquidadBloque
    modo_lote: ModoLoteBloque
