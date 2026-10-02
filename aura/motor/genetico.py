"""Algoritmo genético de permutaciones con selección, OX y elitismo."""

import random
from itertools import permutations


def cruce_ox(padre1, padre2, rng):
    """Order crossover: conserva un segmento y completa en el orden del otro padre."""
    n = len(padre1)
    if n < 2:
        return list(padre1), list(padre2)
    a, b = sorted(rng.sample(range(n), 2))

    def hijo(base, relleno):
        h = [None] * n
        h[a : b + 1] = base[a : b + 1]
        faltan = [x for x in relleno[b + 1 :] + relleno[: b + 1] if x not in h]
        posiciones = list(range(b + 1, n)) + list(range(0, a))
        for i, x in zip(posiciones, faltan):
            h[i] = x
        return h

    return hijo(padre1, padre2), hijo(padre2, padre1)


def mutar_intercambio(cromosoma, tasa, rng):
    """Copia antes de mutar para no alterar cromosomas compartidos por referencia."""
    nuevo = list(cromosoma)
    if len(nuevo) > 1 and rng.random() < tasa:
        i, j = rng.sample(range(len(nuevo)), 2)
        nuevo[i], nuevo[j] = nuevo[j], nuevo[i]
    return nuevo


def genetico(
    ids,
    evaluar_z,
    poblacion=50,
    generaciones=200,
    tasa_mutacion=0.2,
    semilla=42,
    torneo=3,
    objetivo=None,
):
    """Optimiza Z directamente y devuelve cromosoma, valor e historial por generación."""
    rng = random.Random(semilla)
    ids = list(ids)
    if not ids:
        return [], evaluar_z([]), [evaluar_z([])]
    tam = max(2, poblacion)
    pob = []
    for _ in range(tam):
        c = list(ids)
        rng.shuffle(c)
        pob.append(c)
    puntuar = lambda c: evaluar_z(c) if objetivo is None else evaluar_z(c)[objetivo]
    valores = [puntuar(c) for c in pob]
    historial = []
    for _ in range(generaciones):
        historial.append(min(valores))

        def torneo_sel():
            ix = rng.sample(range(len(pob)), min(torneo, len(pob)))
            return list(pob[min(ix, key=lambda i: valores[i])])

        hijos = []
        while len(hijos) < tam:
            h1, h2 = cruce_ox(torneo_sel(), torneo_sel(), rng)
            hijos.extend(
                (
                    mutar_intercambio(h1, tasa_mutacion, rng),
                    mutar_intercambio(h2, tasa_mutacion, rng),
                )
            )
        hijos = hijos[:tam]
        candidatos = pob + hijos
        # Los padres no cambiaron: conservar su fitness evita decodificar el mismo
        # cromosoma en cada generación, a la vez que el elitismo compara padres e hijos.
        vals = valores + [puntuar(c) for c in hijos]
        mejores = sorted(range(len(candidatos)), key=lambda i: vals[i])[:tam]
        pob = [list(candidatos[i]) for i in mejores]
        valores = [vals[i] for i in mejores]
    historial.append(min(valores))
    i = min(range(tam), key=lambda j: valores[j])
    return list(pob[i]), valores[i], historial


def enumerar(ids, evaluar_z):
    """Busca el óptimo exacto; práctico solo hasta seis solicitudes."""
    mejor = None
    z = float("inf")
    for perm in permutations(ids):
        v = evaluar_z(perm)
        if v < z:
            mejor, z = list(perm), v
    return mejor, z
