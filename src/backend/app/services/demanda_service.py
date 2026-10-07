"""Demanda real por tipo de servicio: cuánto se atendió en el tipo ideal y cuánto se desvió.

Un pedido se atiende «con alternativa afín» cuando su servicio ideal era de un tipo y terminó en
un cupo de otro tipo (la afinidad lo permite). Así coordinación ve la demanda real de un tipo
aunque la ocupación de sus servicios parezca media. Solo cuentan las citas que conocen su
servicio ideal (todas las sembradas; las de estudiantes en vivo, si envían `servicio_ideal`).
"""

from collections import Counter

from ..repositories.app_state import AppState
from .etiquetas import Etiquetas


class DemandaService:
    def __init__(self, estado: AppState):
        self._estado = estado
        self._etiquetas = Etiquetas(estado.tablas)

    def _destinos(self, contador: Counter) -> list[dict]:
        return [
            {"tipo": t, "tipo_label": self._etiquetas.tipo(t), "cantidad": n}
            for t, n in sorted(contador.items(), key=lambda kv: (-kv[1], kv[0]))
        ]

    def por_tipo(self, citas: list[dict]) -> list[dict]:
        """Por cada tipo ideal: pedidos, atendidos en su tipo, con alternativa (y a cuál) y sin cupo."""
        tipos = list(self._estado.tablas["afinidad"])
        en_su_tipo = Counter()
        destinos: dict[str, Counter] = {t: Counter() for t in tipos}
        for c in citas:
            ideal = c.get("servicio_ideal")
            if ideal not in destinos:
                continue
            if ideal == c["tipo"]:
                en_su_tipo[ideal] += 1
            else:
                destinos[ideal][c["tipo"]] += 1
        sin_cupo = Counter(d["servicio_ideal"] for d in self._estado.desencuentros)
        filas = []
        for t in tipos:
            con_alternativa = sum(destinos[t].values())
            filas.append(
                {
                    "ideal": t,
                    "ideal_label": self._etiquetas.tipo(t),
                    "pedidos": en_su_tipo[t] + con_alternativa + sin_cupo[t],
                    "atendidos_en_su_tipo": en_su_tipo[t],
                    "atendidos_con_alternativa": con_alternativa,
                    "sin_cupo": sin_cupo[t],
                    "destinos": self._destinos(destinos[t]),
                }
            )
        return filas

    def recibidos_como_alternativa(self, citas_del_servicio: list[dict], tipo: str) -> dict:
        """Citas de este servicio cuyo pedido pedía otro tipo, y de cuál venían."""
        origenes = Counter(
            c["servicio_ideal"]
            for c in citas_del_servicio
            if c.get("servicio_ideal") and c["servicio_ideal"] != tipo
        )
        return {"cantidad": sum(origenes.values()), "origenes": self._destinos(origenes)}
