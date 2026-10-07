from datetime import date

from pydantic import BaseModel


class UmbralesNivel(BaseModel):
    baja_menor_que: float  # ocupación < este valor: baja
    alta_mayor_que: float  # ocupación > este valor: alta (en medio: media)


class EstadoDemo(BaseModel):
    hoy: date
    semana_inicio: date
    semana_fin: date
    agenda_inicio: date  # toda la agenda generada
    agenda_fin: date
    agenda_abierta_inicio: date  # lo que todavía se puede reservar (hoy + 1 …)
    agenda_abierta_fin: date
    escenario: str
    etiqueta: str
    semilla: int
    factor_demanda: float
    proporcion_vespertino_trabaja: float
    umbrales_nivel: UmbralesNivel
