"""Aviso proactivo: ¿se le muestra a esta persona la tarjeta «un espacio para ti» en el campus?

Cuatro señales, cada una vale 1 si se cumple; el aviso exige el puntaje mínimo de `parametros.yaml` (`aviso`):
- S1 Temporada de evaluación: hoy cae en una semana `evaluation_week` de D7 para su institución y distrito.
- S2 Asistencia: la tasa bajó al menos `caida_asistencia` frente al período anterior.
- S3 Nota: el cambio de promedio es menor o igual que `cambio_nota`.
- S4 Carga: sus créditos están en el cuartil superior (`percentil_carga_creditos`) del período.

Sin señal de abandono (D3 `dropout_alert`): esa viene de un dato sintético que no se usa en la plataforma.
El aviso se justifica por contexto (la semana de evaluaciones), nunca por diagnóstico, y la persona puede darlo de baja.
Los datos académicos son los simulados de la demo; con D3 real, S2–S4 saldrían de ahí (`aura/aviso`).
"""

from ..repositories.app_state import AppState
from .academico_service import AcademicoService

NOMBRES = {
    "S1": "Temporada de evaluación",
    "S2": "Caída de asistencia",
    "S3": "Caída de nota",
    "S4": "Carga de créditos alta",
}


class AvisoProactivoService:
    def __init__(self, estado: AppState):
        self._e = estado
        self._aviso = estado.parametros["aviso"]

    def estado(self, estudiante_id: str) -> dict:
        ind = AcademicoService(self._e).indicadores_aviso(estudiante_id)  # 404 si no hay datos de la persona
        cumple = {
            "S1": ind["en_evaluacion"] is not None,
            "S2": ind["variacion_asistencia"] <= -float(self._aviso["caida_asistencia"]) + 1e-9,
            "S3": ind["variacion_nota"] is not None and ind["variacion_nota"] <= float(self._aviso["cambio_nota"]) + 1e-9,
            "S4": ind["creditos"] >= ind["corte_creditos"],
        }
        puntaje = sum(cumple.values())
        minimo = int(self._aviso["puntaje_minimo"])
        # Solo se evalúa durante una semana de evaluaciones (D7), igual que en la validación del aviso.
        elegible = ind["en_evaluacion"] is not None and puntaje >= minimo
        descartado = estudiante_id in self._e.bajas_aviso
        return {
            "mostrar": elegible and not descartado,
            "elegible": elegible,
            "descartado": descartado,
            "puntaje": puntaje,
            "minimo": minimo,
            "senales": [{"id": s, "nombre": NOMBRES[s], "cumple": ok} for s, ok in cumple.items()],
            "semana": ind["en_evaluacion"],
        }

    def dar_de_baja(self, estudiante_id: str) -> dict:
        AcademicoService(self._e).indicadores_aviso(estudiante_id)  # valida que exista
        self._e.bajas_aviso.add(estudiante_id)
        return self.estado(estudiante_id)

    def reactivar(self, estudiante_id: str) -> dict:
        self._e.bajas_aviso.discard(estudiante_id)
        return self.estado(estudiante_id)
