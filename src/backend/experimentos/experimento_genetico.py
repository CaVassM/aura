"""Corre AURA en seis escenarios y resume cinco semillas reproducibles."""

from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import mean, stdev
from time import perf_counter
import argparse, csv, json
from concurrent.futures import ProcessPoolExecutor, as_completed
import yaml

from aura.herramientas.configuracion import ruta_data_pack
from aura.datos.carga import cargar_csv, cargar_servicios, cierres_desde_d7
from aura.motor.agenda import generar_agenda
from aura.motor.reglas import precalcular_opciones, vectorizar_opciones
from aura.motor.fitness import evaluar
from aura.motor.genetico import genetico
from aura.motor.baselines import (
    orden_llegada,
    simular_solicitudes,
    escalar_demanda,
    normalizar_pagos,
    z_normalizado,
    z_plan_b,
    PESOS,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "parametros.yaml"
with CONFIG.open(encoding="utf-8") as archivo:
    PARAMETROS = yaml.safe_load(archivo)
PACK = ruta_data_pack()
OUT = ROOT / "salidas"
METRICAS = (
    "pct_asignados",
    "espera_promedio_dias",
    "espera_diurnos_dias",
    "espera_nocturnos_dias",
    "desencuentros",
)


def escribir_csv(ruta, filas):
    """Escribe CSV en UTF-8 estándar (sin BOM) para preservar tildes."""
    if not filas:
        return
    with ruta.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(filas[0]))
        writer.writeheader()
        writer.writerows(filas)


def calibrar_pagos(ids, evaluar_orden, poblacion, generaciones, semilla):
    """Hace una vez por escenario las cinco optimizaciones monoobjetivo."""
    filas = []
    inicio = perf_counter()
    for i, k in enumerate(PESOS):
        print(f"  calibrando {k} ({i+1}/5)", flush=True)
        crom, _, _ = genetico(
            ids,
            lambda orden: evaluar_orden(orden)[0],
            poblacion,
            generaciones,
            semilla=semilla + 100 + i,
            objetivo=k,
        )
        filas.append(evaluar_orden(crom)[0])
    return normalizar_pagos(filas), filas, perf_counter() - inicio


def resumir(filas, claves):
    """Devuelve media y desviación estándar muestral para cada métrica."""
    salida = {}
    for clave in claves:
        nums = [float(r[clave]) for r in filas]
        salida[f"{clave}_media"] = mean(nums) if nums else 0.0
        salida[f"{clave}_desv_std"] = stdev(nums) if len(nums) > 1 else 0.0
    return salida


def _trabajo_genetico(tarea):
    """Worker independiente: cada tarea ejecuta un GA completo en su proceso."""
    contexto = tarea["contexto"]

    def evaluar_orden(orden):
        return evaluar(
            orden,
            contexto["solicitudes"],
            contexto["opciones"],
            contexto["cupos"],
            contexto["servicios"],
            contexto["libres"],
            contexto["hoy"],
            beta=contexto["beta"],
            horizonte_dias=contexto["horizonte_dias"],
            indice_cupos=contexto["indice_cupos"],
            liberados_servicio=contexto["liberados"],
            opciones_vector=contexto["opciones_vector"],
            indice_vector=contexto["indice_vector"],
        )

    ids = [s.id for s in contexto["solicitudes"]]
    comienzo = perf_counter()
    if tarea["tipo"] == "calibracion":
        crom, _, historial = genetico(
            ids,
            lambda orden: evaluar_orden(orden)[0],
            tarea["poblacion"],
            tarea["generaciones"],
            semilla=tarea["semilla"],
            objetivo=tarea["termino"],
        )
    else:

        def objetivo(orden):
            m = evaluar_orden(orden)[0]
            if tarea["plan_b"]:
                return z_plan_b(m, len(ids), contexto["horizonte_dias"])
            return z_normalizado(m, tarea["zmin"], tarea["zmax"])

        crom, _, historial = genetico(
            ids,
            objetivo,
            tarea["poblacion"],
            tarea["generaciones"],
            semilla=tarea["semilla"],
        )
    metricas, _ = evaluar_orden(crom)
    return {
        "semilla": tarea.get("semilla_base", tarea["semilla"]),
        "cromosoma": crom,
        "historial": historial,
        "metricas": metricas,
        "tiempo_s": perf_counter() - comienzo,
        "termino": tarea.get("termino"),
    }


def correr_escenario(
    nombre,
    factor,
    fraccion,
    generaciones,
    semillas,
    args,
    servicios,
    d2,
    d1,
    d7,
    cierres,
    ocupacion_por_servicio,
):
    """Ejecuta las cinco semillas en paralelo y comparte la tabla de pagos."""
    corridas = []
    utilizaciones = []
    desencuentros = []
    comienzo = perf_counter()
    contextos = []
    baselines = []
    infos = []
    for semilla in semillas:
        print(f"[{nombre}] semilla {semilla}: preparando datos", flush=True)
        hoy = date.fromisoformat(args.hoy)
        solicitudes_base, info = simular_solicitudes(d2, d1, hoy, semilla)
        solicitudes = escalar_demanda(solicitudes_base, factor, semilla)
        cupos, libres = generar_agenda(
            servicios,
            hoy,
            semanas=args.semanas,
            duracion_min=args.duracion_min,
            fraccion_liberada=fraccion,
            ocupacion_inicial=ocupacion_por_servicio,
            semilla=semilla,
            dias_cerrados=cierres,
        )
        indice_cupos = {c.id: c for c in cupos}
        liberados = {s.service_id: 0 for s in servicios}
        for cid in libres:
            liberados[indice_cupos[cid].service_id] += 1
        opciones = precalcular_opciones(solicitudes, cupos, libres, hoy, args.beta)
        opciones_vector, indice_vector = vectorizar_opciones(opciones, cupos)
        contexto = {
            "solicitudes": solicitudes,
            "opciones": opciones,
            "cupos": cupos,
            "servicios": servicios,
            "libres": libres,
            "hoy": hoy,
            "beta": args.beta,
            "horizonte_dias": 7 * args.semanas,
            "indice_cupos": indice_cupos,
            "liberados": liberados,
            "opciones_vector": opciones_vector,
            "indice_vector": indice_vector,
        }
        contextos.append(contexto)
        infos.append(info)
        baselines.append(
            evaluar(
                orden_llegada(solicitudes),
                solicitudes,
                opciones,
                cupos,
                servicios,
                libres,
                hoy,
                beta=args.beta,
                horizonte_dias=7 * args.semanas,
                indice_cupos=indice_cupos,
                liberados_servicio=liberados,
                opciones_vector=opciones_vector,
                indice_vector=indice_vector,
            )[0]
        )
    segundos_calibracion = 0.0
    pago_crudo = []
    zmin = zmax = None
    calibracion_tiempos = {}
    if not args.plan_b:
        tareas = [
            {
                "tipo": "calibracion",
                "contexto": contextos[0],
                "termino": k,
                "poblacion": args.poblacion,
                "generaciones": generaciones,
                "semilla": semillas[0] + 100 + i,
            }
            for i, k in enumerate(PESOS)
        ]
        ini = perf_counter()
        resultados_cal = []
        with ProcessPoolExecutor(max_workers=min(args.workers, len(tareas))) as pool:
            futuros = [pool.submit(_trabajo_genetico, t) for t in tareas]
            for futuro in as_completed(futuros):
                res = futuro.result()
                resultados_cal.append(res)
                print(f"[{nombre}] calibración {res['termino']} lista", flush=True)
        segundos_calibracion = perf_counter() - ini
        por_termino = {r["termino"]: r for r in resultados_cal}
        pago_crudo = [por_termino[k]["metricas"] for k in PESOS]
        calibracion_tiempos = {k: por_termino[k]["tiempo_s"] for k in PESOS}
        zmin, zmax = normalizar_pagos(pago_crudo)
        print(
            f"[{nombre}] cinco calibraciones en paralelo: {segundos_calibracion:.1f} s",
            flush=True,
        )
    tareas = [
        {
            "tipo": "final",
            "contexto": ctx,
            "plan_b": args.plan_b,
            "zmin": zmin,
            "zmax": zmax,
            "poblacion": args.poblacion,
            "generaciones": generaciones,
            "semilla": seed + 1000,
            "semilla_base": seed,
        }
        for ctx, seed in zip(contextos, semillas)
    ]
    resultados_finales = {}
    with ProcessPoolExecutor(max_workers=min(args.workers, len(tareas))) as pool:
        futuros = [pool.submit(_trabajo_genetico, t) for t in tareas]
        for futuro in as_completed(futuros):
            res = futuro.result()
            resultados_finales[res["semilla"]] = res
            print(
                f"[{nombre}] semilla {res['semilla']}: GA {res['tiempo_s']:.1f} s, "
                f"{res['metricas']['pct_asignados']:.1%} asignadas",
                flush=True,
            )
    convergencias = [resultados_finales[s]["historial"] for s in semillas]
    for indice, semilla in enumerate(semillas):
        for metodo, metricas, segundos in (
            ("Llegada", baselines[indice], 0.0),
            (
                "Genético",
                resultados_finales[semilla]["metricas"],
                resultados_finales[semilla]["tiempo_s"],
            ),
        ):
            fila = {
                "escenario": nombre,
                "factor_demanda": factor,
                "fraccion_liberada": fraccion,
                "semilla": semilla,
                "algoritmo": metodo,
                "generaciones": generaciones,
                "solicitudes": metricas["total"],
                "asignados": metricas["asignados"],
                "pct_asignados": metricas["pct_asignados"],
                "espera_promedio_dias": metricas["espera_promedio"],
                "espera_diurnos_dias": metricas["espera_diurnos"],
                "espera_nocturnos_dias": metricas["espera_nocturnos"],
                "desencuentros": metricas["Z1"],
                "Z1": metricas["Z1"],
                "Z2": metricas["Z2"],
                "Z3": metricas["Z3"],
                "Z4": metricas["Z4"],
                "Z5": metricas["Z5"],
                "tiempo_genetico_s": segundos,
                "tiempo_calibracion_compartida_s": (
                    segundos_calibracion if indice == 0 else 0.0
                ),
            }
            corridas.append(fila)
            for sid, u in metricas["utilizacion"].items():
                utilizaciones.append(
                    {
                        "escenario": nombre,
                        "semilla": semilla,
                        "algoritmo": metodo,
                        "service_id": sid,
                        "utilizacion": u,
                    }
                )
            for d in metricas["desencuentros"]:
                desencuentros.append(
                    {
                        "escenario": nombre,
                        "semilla": semilla,
                        "algoritmo": metodo,
                        **{k: str(v) for k, v in d.items()},
                    }
                )
    return {
        "corridas": corridas,
        "utilizaciones": utilizaciones,
        "desencuentros": desencuentros,
        "convergencias": convergencias,
        "calibracion_s": segundos_calibracion,
        "calibracion_por_termino_s": calibracion_tiempos,
        "calibracion_pagos": pago_crudo,
        "tiempo_escenario_s": perf_counter() - comienzo,
        "generaciones": generaciones,
        "fraccion_liberada": fraccion,
        "factor": factor,
        "semana_origen": infos[0],
        "ocupacion_por_servicio": ocupacion_por_servicio,
        "cupos_liberados": [len(ctx["libres"]) for ctx in contextos],
    }


def generar_reporte(escenarios, resumen, uso_resumen, metadatos):
    """Genera el reporte desde los objetos en memoria para evitar fallos de etiquetas."""
    lines = [
        "# Reporte actualizado del motor AURA",
        "",
        f"Fecha base: {metadatos['hoy']}. Réplicas por escenario: {len(metadatos['semillas'])}; "
        f"semillas: {', '.join(map(str,metadatos['semillas']))}.",
        f"Lote base: {metadatos['solicitudes_base']} solicitudes; fracción nocturna "
        f"{metadatos['fraccion_nocturna_base']:.1%}; ocupación histórica media "
        f"{metadatos['ocupacion_historica_promedio']:.1%}.",
        "",
        "Las celdas de métricas muestran media ± desviación estándar muestral entre semillas.",
        "",
        "## Asignación, espera y desencuentros",
        "",
        "| Escenario | Método | % asignadas | Espera (días) | Diurnas | Nocturnas | Desencuentros |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in resumen:

        def pm(k, porcentaje=False):
            x = r[f"{k}_media"]
            sd = r[f"{k}_desv_std"]
            if porcentaje:
                x *= 100
                sd *= 100
            return (
                f"{x:.2f} ± {sd:.2f}" if not porcentaje else f"{x:.1f}% ± {sd:.1f} pp"
            )

        lines.append(
            f"| {r['escenario']} | {r['algoritmo']} | {pm('pct_asignados',True)} | "
            f"{pm('espera_promedio_dias')} | {pm('espera_diurnos_dias')} | "
            f"{pm('espera_nocturnos_dias')} | {pm('desencuentros')} |"
        )
    lines.extend(
        [
            "",
            "## Diferencia emparejada: Genético menos llegada",
            "",
            "Cada diferencia compara los dos métodos con la misma semilla. Es un resumen descriptivo; no es una prueba de significancia.",
            "",
            "| Escenario | Δ asignados (pp) | Δ espera (días) | Δ diurnos | Δ nocturnos | Δ desencuentros |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for nombre, d in escenarios.items():
        por_metodo = {
            m: {r["semilla"]: r for r in d["corridas"] if r["algoritmo"] == m}
            for m in ("Llegada", "Genético")
        }
        paired = {
            k: [
                por_metodo["Genético"][s][k] - por_metodo["Llegada"][s][k]
                for s in por_metodo["Genético"]
            ]
            for k in METRICAS
        }

        def delta(k, scale=1.0):
            vals = [v * scale for v in paired[k]]
            variacion = stdev(vals) if len(vals) > 1 else 0.0
            return f"{mean(vals):+.2f} ± {variacion:.2f}"

        lines.append(
            f"| {nombre} | {delta('pct_asignados',100)} | "
            f"{delta('espera_promedio_dias')} | {delta('espera_diurnos_dias')} | "
            f"{delta('espera_nocturnos_dias')} | {delta('desencuentros')} |"
        )
    lines.extend(
        [
            "",
            "## Utilización media por servicio",
            "",
            "La tabla se construye desde resultados en memoria: las columnas Llegada y Genético "
            "son porcentajes medios entre semillas.",
            "",
            "| Escenario | Servicio | Llegada | Genético |",
            "|---|---|---:|---:|",
        ]
    )
    for nombre in escenarios:
        for sid in sorted(
            {r["service_id"] for r in uso_resumen if r["escenario"] == nombre}
        ):
            vals = {
                r["algoritmo"]: r
                for r in uso_resumen
                if r["escenario"] == nombre and r["service_id"] == sid
            }
            a = vals.get("Llegada", {})
            g = vals.get("Genético", {})
            lines.append(
                f"| {nombre} | {sid} | {a.get('utilizacion_media',0):.1%} ± "
                f"{a.get('utilizacion_desv_std',0):.1%} | {g.get('utilizacion_media',0):.1%} ± "
                f"{g.get('utilizacion_desv_std',0):.1%} |"
            )
    lines.extend(
        [
            "",
            "## Tiempo de ejecución",
            "",
            "`Tiempo GA` es la corrida genética ponderada de cada semilla. La calibración de pagos "
            "se ejecutó una vez por escenario y se comparte entre sus cinco semillas.",
            "",
            "| Escenario | Generaciones | Calibración compartida (s) | Tiempo total del escenario (s) | GA por semilla (s) |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for nombre, d in escenarios.items():
        tiempos = [
            r["tiempo_genetico_s"]
            for r in d["corridas"]
            if r["algoritmo"] == "Genético"
        ]
        lines.append(
            f"| {nombre} | {d['generaciones']} | {d['calibracion_s']:.1f} | "
            f"{d['tiempo_escenario_s']:.1f} | {', '.join(f'{x:.1f}' for x in tiempos)} |"
        )
    lines.extend(
        [
            "",
            "### Tiempo de cada réplica genética",
            "",
            "| Escenario | Semilla | Generaciones | Tiempo GA (s) |",
            "|---|---:|---:|---:|",
        ]
    )
    for nombre, d in escenarios.items():
        for r in d["corridas"]:
            if r["algoritmo"] == "Genético":
                lines.append(
                    f"| {nombre} | {r['semilla']} | {r['generaciones']} | {r['tiempo_genetico_s']:.1f} |"
                )
    lines.extend(
        [
            "",
            "### Tiempo de calibración por término",
            "",
            "Cinco GAs monoobjetivo ejecutados una vez por escenario, en paralelo.",
            "",
            "| Escenario | Z1 (s) | Z2 (s) | Z3 (s) | Z4 (s) | Z5 (s) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for nombre, d in escenarios.items():
        t = d["calibracion_por_termino_s"]
        lines.append(
            f"| {nombre} | " + " | ".join(f"{t.get(k,0):.1f}" for k in PESOS) + " |"
        )
    lines.extend(
        [
            "",
            "## Escenarios y supuestos",
            "",
            "- Demanda evaluada: x1, x2, x4.3, x6 y x8, más x4.3 con 25% de cupos libres liberados.",
            "- Las corridas grandes (x6, x8 y x4.3 con liberación 0.25) usan 500 generaciones; x1, x2 y x4.3 estándar conservan 200.",
            "- Las cinco optimizaciones monoobjetivo que forman la tabla de pagos se corren una vez por escenario; se comparte su normalización para comparar las semillas del mismo escenario.",
            "- El lote base, supuestos de canal/distrito, motivos, agenda y cierres D7 siguen descritos en `README.md`.",
            "- Las cinco semillas miden sensibilidad del lote, la ocupación inicial y el GA. La desviación es muestral (n−1).",
            "- `comparacion.csv` contiene cada semilla; `resumen_5_semillas.csv` agrega medias y desviaciones; `utilizacion_detalle.csv` mantiene la utilización por semilla.",
            "- La convergencia grafica el promedio del mejor Z por generación para cada escenario.",
            "",
            "Para repetir la matriz: `python -m experimentos.experimento_genetico`. Se puede cambiar el conjunto de semillas con `--semillas 42 43 44 45 46`.",
            "",
            "## Herramientas y filtros del aviso",
            "",
            "La demo sin LLM se corre con `python -m experimentos.demo_herramientas`; los esquemas JSON están en `aura.herramientas.esquemas`.",
            "La cobertura, la sensibilidad y la validación agregada con D1 están en `validacion_aviso.md`; los filtros usan D3 y D7, y excluyen D1.",
            "El detalle individual de las señales permanece en el archivo de auditoría interno `aviso_auditoria.csv`.",
            "",
            "El árbol del proyecto y la ruta configurable del Data Pack se documentan en `README.md`.",
        ]
    )
    validacion = OUT / "validacion_aviso.md"
    if validacion.exists():
        lines.extend(["", "## Resultado de validación del aviso", ""])
        lines.extend(validacion.read_text(encoding="utf-8").splitlines()[1:])
    (OUT / "reporte.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hoy", default=PARAMETROS["hoy"])
    parser.add_argument(
        "--data-pack", default=str(PACK), help="Ruta al Data Pack externo"
    )
    parser.add_argument(
        "--salidas", default=str(OUT), help="Carpeta donde se guardan resultados"
    )
    parser.add_argument("--semilla", type=int, default=42)
    parser.add_argument("--semillas", nargs="+", type=int, default=None)
    parser.add_argument(
        "--poblacion", type=int, default=PARAMETROS["experimento"]["poblacion"]
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=PARAMETROS["experimento"]["workers"],
        help="Procesos para correr semillas/objetivos en paralelo",
    )
    parser.add_argument(
        "--generaciones",
        type=int,
        default=None,
        help="Sobrescribe generaciones en todos los escenarios (útil para una corrida rápida)",
    )
    parser.add_argument(
        "--generaciones-grandes",
        type=int,
        default=max(
            fila["generaciones"] for fila in PARAMETROS["experimento"]["escenarios"]
        ),
    )
    parser.add_argument("--semanas", type=int, default=PARAMETROS["horizonte_semanas"])
    parser.add_argument(
        "--duracion-min", type=int, default=PARAMETROS["duracion_sesion_minutos"]
    )
    parser.add_argument("--beta", type=float, default=PARAMETROS["beta"])
    parser.add_argument("--plan-b", action="store_true")
    args = parser.parse_args()
    if args.semillas:
        semillas = args.semillas
    elif args.semilla == 42:
        semillas = PARAMETROS["experimento"]["semillas"]
    else:
        semillas = list(range(args.semilla, args.semilla + 5))
    OUT = Path(args.salidas).resolve()
    hoy = date.fromisoformat(args.hoy)
    OUT.mkdir(parents=True, exist_ok=True)
    pack = Path(args.data_pack).resolve()
    servicios = cargar_servicios(pack / "D6_services_map.geojson")
    d2 = cargar_csv(pack / "D2_support_services.csv")
    d1 = cargar_csv(pack / "D1_wellbeing_survey.csv")
    d7 = cargar_csv(pack / "D7_calendar.csv")
    cierres = cierres_desde_d7(d7)
    fechas = [date.fromisoformat(x["request_date"]) for x in d2]
    semanas_observadas = max(1, (max(fechas) - min(fechas)).days / 7)
    eventos = defaultdict(int)
    for row in d2:
        eventos[row["service_id"]] += 1
    ocupacion = {
        s.service_id: min(
            0.95, eventos[s.service_id] / (semanas_observadas * s.capacidad_semanal)
        )
        for s in servicios
    }
    escenarios_cfg = []
    for fila in PARAMETROS["experimento"]["escenarios"]:
        generaciones = int(fila["generaciones"])
        if generaciones >= 500:
            generaciones = args.generaciones_grandes
        escenarios_cfg.append(
            (
                fila["nombre"],
                float(fila["factor"]),
                float(fila["fraccion_liberada"]),
                generaciones,
            )
        )
    if args.generaciones is not None:
        escenarios_cfg = [(n, f, r, args.generaciones) for n, f, r, _ in escenarios_cfg]
    resultados = {}
    corridas = []
    uso = []
    fallos = []
    for nombre, factor, fraccion, generaciones in escenarios_cfg:
        print(
            f"\n=== {nombre}: demanda x{factor:g}, fracción libre {fraccion:.2f}, "
            f"{generaciones} generaciones, semillas {semillas} ===",
            flush=True,
        )
        data = correr_escenario(
            nombre,
            factor,
            fraccion,
            generaciones,
            semillas,
            args,
            servicios,
            d2,
            d1,
            d7,
            cierres,
            ocupacion,
        )
        resultados[nombre] = data
        corridas.extend(data["corridas"])
        uso.extend(data["utilizaciones"])
        fallos.extend(data["desencuentros"])
    resumen = []
    for nombre, _, _, _ in escenarios_cfg:
        for metodo in ("Llegada", "Genético"):
            grupo = [
                r
                for r in corridas
                if r["escenario"] == nombre and r["algoritmo"] == metodo
            ]
            fila = {
                "escenario": nombre,
                "algoritmo": metodo,
                "semillas": len(semillas),
                "generaciones": resultados[nombre]["generaciones"],
            }
            fila.update(resumir(grupo, METRICAS))
            resumen.append(fila)
    uso_resumen = []
    for nombre, _, _, _ in escenarios_cfg:
        for metodo in ("Llegada", "Genético"):
            for sid in (s.service_id for s in servicios):
                grupo = [
                    r
                    for r in uso
                    if r["escenario"] == nombre
                    and r["algoritmo"] == metodo
                    and r["service_id"] == sid
                ]
                fila = {"escenario": nombre, "algoritmo": metodo, "service_id": sid}
                fila.update(resumir(grupo, ("utilizacion",)))
                uso_resumen.append(fila)
    escribir_csv(OUT / "comparacion.csv", corridas)
    escribir_csv(OUT / "resumen_5_semillas.csv", resumen)
    escribir_csv(OUT / "utilizacion_por_servicio.csv", uso_resumen)
    escribir_csv(OUT / "utilizacion_detalle.csv", uso)
    escribir_csv(OUT / "desencuentros.csv", fallos)
    metadatos = {
        "hoy": str(hoy),
        "semillas": semillas,
        "poblacion": args.poblacion,
        "workers": args.workers,
        "escenarios": {
            n: {
                "factor": f,
                "fraccion_liberada": r,
                "generaciones": g,
                "segundos_calibracion": resultados[n]["calibracion_s"],
                "segundos_calibracion_por_termino": resultados[n][
                    "calibracion_por_termino_s"
                ],
                "segundos_escenario": resultados[n]["tiempo_escenario_s"],
            }
            for n, f, r, g in escenarios_cfg
        },
        "solicitudes_base": resultados[escenarios_cfg[0][0]]["semana_origen"][
            "n_semana"
        ],
        "semana_origen": resultados[escenarios_cfg[0][0]]["semana_origen"],
        "fraccion_nocturna_base": sum(
            s.grupo == "nocturno"
            for s in simular_solicitudes(d2, d1, hoy, semillas[0])[0]
        )
        / max(1, resultados[escenarios_cfg[0][0]]["semana_origen"]["n_semana"]),
        "ocupacion_historica_promedio": mean(ocupacion.values()),
        "eventos_cierre_D7": sum(
            row.get("event_type", "").lower()
            in {
                "holiday",
                "feriado",
                "closure",
                "closed",
                "service_closed",
                "cierre_servicio",
            }
            for row in d7
        ),
        "plan_b": args.plan_b,
    }
    (OUT / "metadatos.json").write_text(
        json.dumps(metadatos, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    generar_reporte(resultados, resumen, uso_resumen, metadatos)
    try:
        import matplotlib.pyplot as plt

        for nombre, data in resultados.items():
            n = min(map(len, data["convergencias"]))
            media = [mean(h[i] for h in data["convergencias"]) for i in range(n)]
            plt.plot(range(n), media, label=nombre)
        plt.xlabel("Generación")
        plt.ylabel("Promedio del mejor Z")
        plt.title("Convergencia media entre semillas")
        plt.legend()
        plt.tight_layout()
        plt.savefig(OUT / "convergencia.png", dpi=160)
        plt.close()
    except ImportError:
        print("matplotlib no está instalado; se omitió el gráfico.")
    print("\nCorridas completadas. Archivos UTF-8 guardados en", OUT, flush=True)
    for r in resumen:
        print(
            f"{r['escenario']} {r['algoritmo']}: {r['pct_asignados_media']:.1%} ± "
            f"{r['pct_asignados_desv_std']:.1%}; espera {r['espera_promedio_dias_media']:.2f} ± "
            f"{r['espera_promedio_dias_desv_std']:.2f} d",
            flush=True,
        )


if __name__ == "__main__":
    main()
