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
            "S1": aviso["caida_asistencia"],
            "S2": aviso["cambio_nota"],
            "S3": aviso["percentil_carga_creditos"],
        }  # la semana de evaluaciones (D7) es la condición del aviso, no una señal
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
                "total_senales": len(umbrales),
                "regla": et.aviso_regla.format(minimo=aviso["puntaje_minimo"], total=len(umbrales)),
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
            "equidad": {
                "provisional": prov.get("equidad", False),
                "max_citas_activas_por_tipo": int(p.get("max_citas_activas_por_tipo", 1)),
            },
            "modo_lote": {
                "provisional": prov.get("modo_lote", False),
                "umbral_pct": round(100 * float(p["modo_lote_umbral_utilizacion"]), 1),
                "ventana_s": int(p["lote"]["ventana_segundos"]),
                "tamano_maximo": int(p["lote"]["tamano_maximo"]),
                "max_opciones": int(p.get("max_opciones", 3)),
            },
            "pesos": {
                "provisional": prov["pesos"],
                "terminos": [
                    {"id": z, "nombre": et.pesos[z], "peso": peso}
                    for z, peso in p["pesos_z"].items()
                ],
            },
        }
