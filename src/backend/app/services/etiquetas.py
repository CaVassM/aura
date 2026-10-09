"""Etiquetas en español y utilidades de presentación, leídas de `etiquetas` en tablas.yaml."""

from itertools import groupby


class Etiquetas:
    """Traduce códigos de datos (tipo, motivo, canal, grupo, día) a texto para la API."""

    def __init__(self, tablas: dict):
        self._e = tablas["etiquetas"]

    def _de(self, bloque: str, codigo: str) -> str:
        return self._e[bloque].get(codigo, codigo)

    def tipo(self, codigo: str) -> str:
        return self._de("tipo", codigo)

    def motivo(self, codigo: str) -> str:
        return self._de("motivo", codigo) if codigo else ""

    def canal(self, codigo: str) -> str:
        return self._de("canal", codigo)

    def grupo(self, codigo: str) -> str:
        return self._de("grupo", codigo)

    def grupo_plural(self, codigo: str) -> str:
        return self._de("grupo_plural", codigo)

    def nivel(self, codigo: str) -> str:
        return self._de("nivel", codigo)

    def dia(self, indice: int) -> str:
        return self._e["dias_semana"][indice]

    def dia_largo(self, indice: int) -> str:
        return self._e["dias_semana_largo"][indice]

    def dias_texto(self, indices: list[int]) -> str:
        """`Lun–Vie` si los días son consecutivos (3 o más); si no, `Lun, Mié`."""
        dias = sorted(set(indices))
        consecutivos = all(b - a == 1 for a, b in zip(dias, dias[1:]))
        if len(dias) >= 3 and consecutivos:
            return f"{self.dia(dias[0])}–{self.dia(dias[-1])}"
        return ", ".join(self.dia(d) for d in dias)

    def dias_texto_largo(self, indices: list[int]) -> str:
        """`lunes a viernes` si los días son consecutivos (3 o más); si no, `lunes, miércoles`."""
        dias = sorted(set(indices))
        nombres = self._e["dias_semana_largo"]
        if len(dias) >= 3 and all(b - a == 1 for a, b in zip(dias, dias[1:])):
            return f"{nombres[dias[0]]} a {nombres[dias[-1]]}"
        return ", ".join(nombres[d] for d in dias)

    def horario_texto(self, horario: list[dict]) -> str:
        """`Lun–Vie · 09:00–18:00`; varios tramos se separan con `; `."""
        tramos = []
        ordenado = sorted(horario, key=lambda h: (h["desde"], h["hasta"], h["dia"]))
        for (desde, hasta), grupo in groupby(ordenado, key=lambda h: (h["desde"], h["hasta"])):
            dias = self.dias_texto([h["dia"] for h in grupo])
            tramos.append(f"{dias} · {desde}–{hasta}")
        return "; ".join(tramos)

    def horario_estructurado(self, horario: list[dict]) -> list[dict]:
        """Tramos con sus días: `[{"dias": ["Lun", ...], "desde": "09:00", "hasta": "18:00"}]`."""
        ordenado = sorted(horario, key=lambda h: (h["desde"], h["hasta"], h["dia"]))
        return [
            {"dias": [self.dia(h["dia"]) for h in grupo], "desde": desde, "hasta": hasta}
            for (desde, hasta), grupo in groupby(
                ordenado, key=lambda h: (h["desde"], h["hasta"])
            )
        ]

    def valor(self, codigo) -> str:
        """Traduce un valor técnico de los datos (p. ej. `medium` → `media`); lo desconocido queda igual."""
        return self._e["valores"].get(str(codigo), str(codigo))

    @property
    def dias_semana(self) -> list[str]:
        return list(self._e["dias_semana"])

    @property
    def pesos(self) -> dict:
        return self._e["pesos"]

    @property
    def senales(self) -> dict:
        return self._e["senales"]

    @property
    def franja_principal(self) -> str:
        return self._e["franja_principal"]

    @property
    def insight(self) -> str:
        return self._e["insight"]

    @property
    def insight_vacio(self) -> str:
        return self._e["insight_vacio"]
