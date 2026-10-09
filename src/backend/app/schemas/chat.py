"""Chat con el agente conversacional (vista del estudiante)."""

from pydantic import BaseModel, Field

from .citas import CitaOut, LoteOfertaOut, OpcionOut
from .lotes import LoteEstadoOut


class ChatIn(BaseModel):
    mensaje: str = Field(min_length=1, max_length=2000, examples=["Estoy estresada por los parciales"])
    estudiante_id: str = Field(examples=["STU_DEMO_001"])
    session_id: str | None = Field(
        default=None, description="Omítelo en el primer mensaje; reutiliza el que devuelve la respuesta"
    )
    distrito: str | None = Field(
        default=None, examples=["DIST_GAIA"], description="Opcional: si el portal ya lo conoce, el agente no lo pregunta"
    )
    grupo: str | None = Field(default=None, pattern="^(diurno|nocturno)$", description="Opcional: turno de la persona")


class HerramientaUsadaOut(BaseModel):
    nombre: str
    ok: bool


class ChatOut(BaseModel):
    session_id: str
    respuesta: str = Field(description="Texto del agente para mostrar en la burbuja")
    opciones: list[OpcionOut] = Field(
        default=[], description="Si el agente acaba de proponer citas: tarjetas para mostrar (sin reservar)"
    )
    cita: CitaOut | None = Field(default=None, description="Cita reservada en este mensaje")
    cita_cancelada: CitaOut | None = Field(default=None, description="Cita cancelada en este mensaje")
    desencuentro_registrado: bool = False
    lote: LoteEstadoOut | None = Field(
        default=None, description="La persona quedó esperando en un lote: cuenta regresiva hasta que se cierre solo"
    )
    lote_oferta: LoteOfertaOut | None = Field(
        default=None, description="Todo lo compatible está en servicios en modo lote: el agente ofrece entrar al lote"
    )
    lista_espera: dict | None = Field(
        default=None, description="La persona quedó en la lista de espera: se le avisará aquí si se libera un cupo (`{id, ...}`)"
    )
    alerta_crisis: bool = Field(default=False, description="El mensaje activó el protocolo de ayuda inmediata")
    herramientas_usadas: list[HerramientaUsadaOut] = []


class MensajeOut(BaseModel):
    rol: str = Field(description="`user` o `agent`")
    texto: str


class HistorialOut(BaseModel):
    session_id: str
    mensajes: list[MensajeOut]


class ChatEstadoOut(BaseModel):
    modelo: str
    url: str
    dependencias_instaladas: bool
    ollama_disponible: bool
    modelo_instalado: bool
    detalle: str
