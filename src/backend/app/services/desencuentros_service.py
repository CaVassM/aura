"""Desencuentros: solicitudes que el motor no pudo atender, con filtros, heatmap e insight."""

import csv
import io
from collections import Counter
from math import ceil

from ..repositories.app_state import AppState
from .etiquetas import Etiquetas

COLUMNAS_CSV = [
    "id", "fecha", "motivo", "motivo_label", "servicio_ideal", "servicio_ideal_label",
    "distrito", "franja_dia", "franja_desde", "franja_hasta", "canales_aceptables", "grupo",
]  # fmt: skip


def _minutos(hhmm: str) -> int:
    horas, minutos = hhmm.split(":")
    return int(horas) * 60 + int(minutos)


class DesencuentrosService:
    def __init__(self, estado: AppState):
        self._estado = estado
        self._etiquetas = Etiquetas(estado.tablas)

    # --- Presentación de un registro ---

    def _franja(self, registro: dict) -> dict:
        """Primer tramo horario del registro, con sus días agrupados (`Lun–Vie`)."""
        franjas = registro["franjas"]
        primera = franjas[0]
        dias = [
            f["dia_semana"]
            for f in franjas
            if (f["desde"], f["hasta"]) == (primera["desde"], primera["hasta"])
        ]
        return {
            "dia": self._etiquetas.dias_texto(dias),
            "desde": primera["desde"],
            "hasta": primera["hasta"],
        }

    def item(self, registro: dict) -> dict:
        et = self._etiquetas
        return {
            "id": registro["registro_id"],
            "fecha": registro["fecha"],
            "motivo": registro["motivo"],
            "motivo_label": et.motivo(registro["motivo"]),
            "servicio_ideal": registro["servicio_ideal"],
            "servicio_ideal_label": et.tipo(registro["servicio_ideal"]),
            "distrito": registro["distrito"],
            "franja": self._franja(registro),
            "canales_aceptables": registro["canales_aceptables"],
            "canales_label": [et.canal(c) for c in registro["canales_aceptables"]],
            "grupo": registro["grupo"],
            "grupo_label": et.grupo(registro["grupo"]),
        }

    # --- Consultas ---

    def _filtrar(self, motivo, distrito, servicio_ideal, grupo) -> list[dict]:
        criterios = {
            "motivo": motivo,
            "distrito": distrito,
            "servicio_ideal": servicio_ideal,
            "grupo": grupo,
        }
        registros = [
            r
            for r in self._estado.desencuentros
            if all(valor is None or r[campo] == valor for campo, valor in criterios.items())
        ]
        return sorted(registros, key=lambda r: (r["fecha"], r["registro_id"]), reverse=True)

    def listar(self, motivo=None, distrito=None, servicio_ideal=None, grupo=None,
               pagina: int = 1, tamano: int = 8) -> dict:  # fmt: skip
        filtrados = self._filtrar(motivo, distrito, servicio_ideal, grupo)
        inicio = (pagina - 1) * tamano
        return {
            "total": len(self._estado.desencuentros),
            "filtrados": len(filtrados),
            "pagina": pagina,
            "paginas": max(1, ceil(len(filtrados) / tamano)),
            "items": [self.item(r) for r in filtrados[inicio : inicio + tamano]],
            "heatmap": self._heatmap(filtrados),
            "insight": self._insight(filtrados),
        }

    def recientes(self, tipo: str, distrito: str) -> list[dict]:
        """Desencuentros más recientes cuyo servicio ideal es `tipo`, en el distrito dado."""
        cantidad = self._estado.parametros["coordinacion"]["desencuentros_recientes"]
        return [
            self.item(r) for r in self._filtrar(None, distrito, tipo, None)[:cantidad]
        ]

    def csv(self, motivo=None, distrito=None, servicio_ideal=None, grupo=None) -> str:
        salida = io.StringIO()
        escritor = csv.DictWriter(salida, fieldnames=COLUMNAS_CSV, lineterminator="\n")
        escritor.writeheader()
        for registro in self._filtrar(motivo, distrito, servicio_ideal, grupo):
            i = self.item(registro)
            escritor.writerow(
                {
                    "id": i["id"], "fecha": i["fecha"], "motivo": i["motivo"],
                    "motivo_label": i["motivo_label"],
                    "servicio_ideal": i["servicio_ideal"],
                    "servicio_ideal_label": i["servicio_ideal_label"],
                    "distrito": i["distrito"],
                    "franja_dia": i["franja"]["dia"],
                    "franja_desde": i["franja"]["desde"],
                    "franja_hasta": i["franja"]["hasta"],
                    "canales_aceptables": ";".join(i["canales_aceptables"]),
                    "grupo": i["grupo"],
                }
            )  # fmt: skip
        return salida.getvalue()

    # --- Agregados sobre el conjunto filtrado ---

    def _heatmap(self, registros: list[dict]) -> dict:
        """Cuenta, por día y hora, las solicitudes cuya franja cubre esa hora."""
        cfg = self._estado.parametros["coordinacion"]
        primera, ultima = cfg["horas_heatmap"]
        horas = list(range(primera, ultima + 1))
        dias = self._etiquetas.dias_semana[: cfg["dias_heatmap"]]
        celdas = [[0] * len(horas) for _ in dias]
        for registro in registros:
            cubiertas = set()
            for franja in registro["franjas"]:
                desde, hasta = _minutos(franja["desde"]), _minutos(franja["hasta"])
                for j, hora in enumerate(horas):
                    if franja["dia_semana"] < len(dias) and desde < (hora + 1) * 60 and hasta > hora * 60:
                        cubiertas.add((franja["dia_semana"], j))
            for dia, j in cubiertas:
                celdas[dia][j] += 1
        return {"dias": dias, "horas": horas, "celdas": celdas}

    def _insight(self, registros: list[dict]) -> dict:
        """Combinación (grupo, servicio ideal, franja) más frecuente, en una frase."""
        if not registros:
            return {
                "texto": self._etiquetas.insight_vacio,
                "porcentaje": 0.0,
                "grupo": None,
                "servicio_ideal": None,
                "franja": None,
            }
        combinaciones = Counter()
        for r in registros:
            f = self._franja(r)
            combinaciones[(r["grupo"], r["servicio_ideal"], f["dia"], f["desde"], f["hasta"])] += 1
        (grupo, tipo, dia, desde, hasta), cuenta = sorted(
            combinaciones.items(), key=lambda kv: (-kv[1], kv[0])
        )[0]
        pct = round(100 * cuenta / len(registros), 1)
        servicio = self._etiquetas.tipo(tipo)
        texto = self._etiquetas.insight.format(
            pct=f"{pct:g}".replace(".", ","),
            grupo=self._etiquetas.grupo_plural(grupo),
            servicio=servicio[:1].lower() + servicio[1:],
            desde=desde,
            hasta=hasta,
        )
        return {
            "texto": texto,
            "porcentaje": pct,
            "grupo": grupo,
            "servicio_ideal": tipo,
            "franja": {"dia": dia, "desde": desde, "hasta": hasta},
        }
