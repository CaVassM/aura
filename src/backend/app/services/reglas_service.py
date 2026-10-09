"""Reglas del motor en solo lectura, tal como están en los YAML."""

from ..repositories.app_state import AppState
from .etiquetas import Etiquetas


class ReglasService:
    def __init__(self, estado: AppState):
        self._p = estado.parametros
        self._t = estado.tablas
        self._et = Etiquetas(estado.tablas)

    def reglas(self) -> dict:
        et, p, t = self._et, self._p, self._t

        def texto_umbral(umbral) -> str:
            """Umbral en español: `media o alta`, `0,05`, `−0,5`."""
            if isinstance(umbral, list):
                return " o ".join(et.valor(u) for u in umbral)
            if isinstance(umbral, (int, float)):
                return str(umbral).replace(".", ",").replace("-", "−")
            return et.valor(umbral)
        prov = t["provisional"]
        tipos = list(t["afinidad"])
        aviso = p["aviso"]
        umbrales = {
            "S1": aviso["evento_evaluacion"],  # temporada de evaluación (D7); la alerta de abandono de D3 ya no es señal
            "S2": aviso["caida_asistencia"],
            "S3": aviso["cambio_nota"],
            "S4": aviso["percentil_carga_creditos"],
        }
        return {
            "motivo_servicio": {
                "provisional": prov["motivo_servicio"],
                "items": [
                    {
                        "motivo": motivo,
                        "motivo_label": et.motivo(motivo),
                        "servicio": tipo,
                        "servicio_label": et.tipo(tipo),
                    }
                    for motivo, tipo in t["motivo_a_servicio"].items()
                ],
            },
            "afinidad": {
                "provisional": prov["afinidad"],
                "minimo_alternativa": p["umbral_afinidad"],
                "minimo_provisional": prov["umbral_afinidad"],
                "tipos": [{"codigo": c, "label": et.tipo(c)} for c in tipos],
                "matriz": [
                    {
                        "ideal": ideal,
                        "ideal_label": et.tipo(ideal),
                        "valores": [
                            {"tipo": c, "tipo_label": et.tipo(c), "valor": t["afinidad"][ideal][c]}
                            for c in tipos
                        ],
                    }
                    for ideal in tipos
                ],
            },
            "aviso": {
                "provisional": prov["aviso"],
                "puntaje_minimo": aviso["puntaje_minimo"],
                "solo_semanas_evaluacion": bool(aviso.get("evento_evaluacion")),
                "evento_evaluacion": aviso.get("evento_evaluacion"),
                "senales": [
                    {
                        "id": sid,
                        "nombre": et.senales[sid]["nombre"],
                        "descripcion": et.senales[sid]["descripcion"].format(
                            umbral=texto_umbral(umbral)
                        ),
                        "umbral": umbral,
                        "umbral_texto": texto_umbral(umbral),
                    }
                    for sid, umbral in umbrales.items()
                ],
            },
            "p_asistencia": {
                "provisional": prov["p_asistencia"],
                "canales": [
                    {"canal": c, "canal_label": et.canal(c), "valor": v}
                    for c, v in p["probabilidad_canal"].items()
                ],
            },
            "pesos": {
                "provisional": prov["pesos"],
                "terminos": [
                    {"id": z, "nombre": et.pesos[z], "peso": peso}
                    for z, peso in p["pesos_z"].items()
                ],
            },
        }
