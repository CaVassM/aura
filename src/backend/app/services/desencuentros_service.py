"""Desencuentros: solicitudes que el motor no pudo atender, con filtros, matriz distrito × servicio e insight."""

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
            "matriz_distrito_servicio": self._matriz(filtrados),
            "franja_principal": self._franja_principal(filtrados),
            "insight": self._insight(self._filtrar(None, None, None, None)),  # siempre sobre el total
            "insight_filtro": (
                self._insight(filtrados) if any((motivo, distrito, servicio_ideal, grupo)) else None
            ),
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

    def _matriz(self, registros: list[dict]) -> dict:
        """Conteo de desencuentros por distrito (filas) y servicio ideal (columnas), con totales."""
        distritos = sorted({s["distrito"] for s in self._estado.motor.servicios()})
        tipos = list(self._estado.tablas["afinidad"])
        cuenta = Counter((r["distrito"], r["servicio_ideal"]) for r in registros)
        celdas = [[cuenta[(d, t)] for t in tipos] for d in distritos]
        return {
            "distritos": distritos,
            "servicios": [{"tipo": t, "label": self._etiquetas.tipo(t)} for t in tipos],
            "celdas": celdas,
            "total_filas": [sum(fila) for fila in celdas],
            "total_columnas": [sum(fila[j] for fila in celdas) for j in range(len(tipos))],
            "total": sum(map(sum, celdas)),
        }

    def _franja_principal(self, registros: list[dict]) -> dict | None:
        """La franja (horas y días) que más declaran los pedidos del conjunto, y qué porcentaje es."""
        if not registros:
            return None
        cuenta = Counter()
        for r in registros:
            primera = r["franjas"][0]
            dias = tuple(
                f["dia_semana"]
                for f in r["franjas"]
                if (f["desde"], f["hasta"]) == (primera["desde"], primera["hasta"])
            )
            cuenta[(primera["desde"], primera["hasta"], dias)] += 1
        (desde, hasta, dias), n = sorted(cuenta.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        dias_texto = self._etiquetas.dias_texto_largo(list(dias))
        return {
            "texto": self._etiquetas.franja_principal.format(desde=desde, hasta=hasta, dias=dias_texto),
            "porcentaje": round(100 * n / len(registros), 1),
            "desde": desde,
            "hasta": hasta,
            "dias": dias_texto,
        }

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
