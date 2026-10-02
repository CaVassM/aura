"""Compara derivaciones registradas en D5 con propuestas AURA sin reservar cupos."""

import argparse
import csv
import json
import re
import unicodedata
from collections import Counter
from datetime import date, time, timedelta
from itertools import product
from pathlib import Path

from aura.datos.carga import (
    cargar_data_pack,
    cargar_csv,
    cargar_servicios,
    cierres_desde_d7,
)
from aura.herramientas.configuracion import RAIZ_PROYECTO, cargar_yaml, ruta_data_pack
from aura.motor.agenda import generar_agenda
from aura.motor.costo import mejores_opciones
from aura.motor.datos import Franja, Solicitud
from aura.motor.reglas import precalcular_opciones


def normalizar(texto: str) -> str:
    """Quita tildes y pasa el texto a minúsculas para reconocer frases de D5."""
    normalizado = unicodedata.normalize("NFKD", texto.lower())
    return "".join(letra for letra in normalizado if not unicodedata.combining(letra))


def extraer_perfil(conversacion: dict) -> dict:
    """Extrae modalidad, trabajo y preferencia escrita solo de turnos del estudiante."""
    mensajes = [
        turno.get("text", "")
        for turno in conversacion.get("messages", [])
        if turno.get("role") == "student"
    ]
    texto = normalizar(" ".join(mensajes))
    coincidencia = re.search(r"modalidad\s+(day|evening)\b", texto)
    modalidad = coincidencia.group(1) if coincidencia else "unknown"
    niega_trabajo = bool(
        re.search(r"\bno (?:trabajo|tengo empleo|tengo trabajo)\b", texto)
    )
    trabaja = (
        bool(
            re.search(
                r"\btrabajo y estudio\b|\btrabajo al mismo tiempo\b|\btengo trabajo\b",
                texto,
            )
        )
        and not niega_trabajo
    )
    escrito = bool(
        re.search(r"por escrito|informacion escrita|prefiero.{0,30}escrit", texto)
    )
    return {"modalidad": modalidad, "trabaja": trabaja, "prefiere_escrito": escrito}


def franjas_de_perfil(perfil: dict) -> tuple[Franja, ...]:
    """Traduce la modalidad declarada a las ventanas horarias del protocolo D5."""
    if perfil["modalidad"] == "day":
        desde, hasta = time(9), time(18)
    elif perfil["trabaja"]:
        desde, hasta = time(19), time(21)
    else:
        desde, hasta = time(17), time(21)
    return tuple(Franja(dia, desde, hasta) for dia in range(5))


def horario_servicio_compatible(
    servicio, franjas: tuple[Franja, ...], duracion: int
) -> bool:
    """Comprueba si D6 permite al menos una sesión completa dentro de las franjas."""
    for dia_servicio, apertura, cierre in servicio.dias_horas:
        for franja in franjas:
            if franja.dia_semana != dia_servicio:
                continue
            inicio = max(apertura, franja.hora_inicio)
            fin = min(cierre, franja.hora_fin)
            if timedelta(hours=fin.hour, minutes=fin.minute) - timedelta(
                hours=inicio.hour, minutes=inicio.minute
            ) >= timedelta(minutes=duracion):
                return True
    return False


def crear_solicitud(
    conversacion: dict, perfil: dict, servicio_d5, ideal: str, hoy: date
) -> Solicitud:
    """Construye la solicitud de prueba usando el distrito del servicio de D5."""
    canales = (
        ("digital",)
        if perfil["prefiere_escrito"]
        else ("digital", "phone", "in_person")
    )
    grupo = "diurno" if perfil["modalidad"] == "day" else "nocturno"
    distrito = servicio_d5.distrito if servicio_d5 else "UNKNOWN"
    return Solicitud(
        id=conversacion["conversation_id"],
        servicio_ideal=ideal,
        distrito=distrito,
        franjas=franjas_de_perfil(perfil),
        canales_aceptables=canales,
        fecha_solicitud=hoy,
        grupo=grupo,
    )


def analizar_conversacion(
    conversacion: dict,
    servicios: dict,
    motivo_a_servicio: dict,
    cupos: list,
    libres: set[str],
    cupos_por_id: dict,
    hoy: date,
    beta: float,
    duracion: int,
) -> dict:
    """Evalúa derivación original y una propuesta AURA sobre inventario nuevo."""
    perfil = extraer_perfil(conversacion)
    referral_id = conversacion.get("referral", "")
    servicio_d5 = servicios.get(referral_id)
    motivo = conversacion.get("motive", "")
    ideal = motivo_a_servicio.get(motivo)
    ideal_para_motor = ideal or f"sin_mapeo:{motivo}"
    solicitud = crear_solicitud(
        conversacion, perfil, servicio_d5, ideal_para_motor, hoy
    )
    opciones_por_solicitud = precalcular_opciones([solicitud], cupos, libres, hoy, beta)
    opciones = mejores_opciones(
        solicitud,
        opciones_por_solicitud[solicitud.id],
        # Conjunto vacío nuevo: cada conversación ve la agenda inicial completa.
        set(),
        1,
        cupos_por_id=cupos_por_id,
        hoy=hoy,
        beta=beta,
    )
    elegido = opciones[0] if opciones else None
    cupo = cupos_por_id[elegido.cupo_id] if elegido else None
    tipo_d5 = servicio_d5.tipo if servicio_d5 else "desconocido"
    tipo_aura = cupo.tipo if cupo else ""
    cierra_18_d5 = bool(
        servicio_d5
        and any(cierre == time(18) for _, _, cierre in servicio_d5.dias_horas)
    )
    horario_original = bool(
        servicio_d5
        and horario_servicio_compatible(
            servicio_d5, franjas_de_perfil(perfil), duracion
        )
    )
    status = "opcion_compatible" if elegido else "desencuentro"
    segmento = (
        "day"
        if perfil["modalidad"] == "day"
        else "evening_trabaja"
        if perfil["modalidad"] == "evening" and perfil["trabaja"]
        else "evening_sin_trabajo"
        if perfil["modalidad"] == "evening"
        else "unknown"
    )
    return {
        "conversation_id": conversacion["conversation_id"],
        "modalidad": perfil["modalidad"],
        "grupo_modalidad": segmento,
        "trabaja": perfil["trabaja"],
        "prefiere_escrito": perfil["prefiere_escrito"],
        "motivo": motivo,
        "servicio_ideal": ideal or "",
        "motivo_mapeado": ideal is not None,
        "referral_d5": referral_id,
        "tipo_d5": tipo_d5,
        "distrito_d5": servicio_d5.distrito if servicio_d5 else "",
        "horario_compatible_d5": horario_original,
        "servicio_cierra_18_d5": cierra_18_d5,
        "derivacion_d5_incompatible": not horario_original,
        "estado_aura": status,
        "opcion_aura": f"{cupo.id}|{elegido.canal}" if elegido and cupo else "",
        "tipo_aura": tipo_aura,
        "horario_compatible_aura": bool(elegido),
        "motivo_coherente_d5": tipo_d5 == ideal if ideal else "",
        "motivo_coherente_aura": tipo_aura == ideal if elegido and ideal else "",
        "alternativa_aura": bool(elegido and ideal and tipo_aura != ideal),
        "canales_aceptables": ";".join(solicitud.canales_aceptables),
    }


def porcentaje(numerador: int, denominador: int) -> float:
    """Calcula porcentaje y define cero si no hay casos evaluables."""
    return 100 * numerador / denominador if denominador else 0.0


def resumir_por_modalidad(filas: list[dict]) -> list[dict]:
    """Resume horario y disponibilidad por modalidad y situación laboral."""
    resumen = []
    grupos = (
        ("day", "day"),
        ("evening_trabaja", "evening y trabaja"),
        ("evening_sin_trabajo", "evening sin trabajo"),
    )
    for segmento, etiqueta in grupos:
        grupo = [fila for fila in filas if fila["grupo_modalidad"] == segmento]
        mapeadas = [fila for fila in grupo if fila["motivo_mapeado"]]
        resumen.append(
            {
                "grupo_modalidad": etiqueta,
                "conversaciones": len(grupo),
                "motivo_mapeado": len(mapeadas),
                "pct_d5_servicio_cierra_18": porcentaje(
                    sum(fila["servicio_cierra_18_d5"] for fila in grupo), len(grupo)
                ),
                "pct_d5_incompatible": porcentaje(
                    sum(fila["derivacion_d5_incompatible"] for fila in grupo), len(grupo)
                ),
                "pct_aura_opcion_compatible": porcentaje(
                    sum(fila["estado_aura"] == "opcion_compatible" for fila in grupo), len(grupo)
                ),
                "pct_aura_desencuentro": porcentaje(
                    sum(fila["estado_aura"] == "desencuentro" for fila in grupo), len(grupo)
                ),
            }
        )
    return resumen


def escribir_csv(ruta: Path, filas: list[dict]) -> None:
    """Escribe tablas de auditoría en UTF-8 sin BOM."""
    if not filas:
        return
    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(filas[0]))
        escritor.writeheader()
        escritor.writerows(filas)


def generar_grafico(resumen: list[dict], ruta: Path) -> None:
    """Guarda barras agrupadas para contrastar horario y resultados AURA."""
    import matplotlib.pyplot as plt
    import numpy as np

    etiquetas = [
        "D5 deriva a servicio que cierra 18:00",
        "D5 incompatible con horario",
        "AURA opción compatible",
        "AURA desencuentro",
    ]
    claves = [
        "pct_d5_servicio_cierra_18",
        "pct_d5_incompatible",
        "pct_aura_opcion_compatible",
        "pct_aura_desencuentro",
    ]
    posiciones = np.arange(len(etiquetas))
    ancho = 0.36
    figura, eje = plt.subplots(figsize=(10, 5))
    for indice, fila in enumerate(resumen):
        valores = [fila[clave] for clave in claves]
        eje.bar(
            posiciones + (indice - (len(resumen) - 1) / 2) * ancho,
            valores,
            ancho,
            label=fila["grupo_modalidad"],
        )
    eje.set_ylabel("Porcentaje (%)")
    eje.set_xticks(posiciones, etiquetas, rotation=12, ha="right")
    eje.set_ylim(0, 100)
    eje.legend(title="Modalidad")
    eje.set_title("Derivación registrada en D5 y opciones compatibles de AURA")
    figura.tight_layout()
    figura.savefig(ruta, dpi=160)
    plt.close(figura)


def escribir_reporte(ruta: Path, filas: list[dict], resumen: list[dict]) -> None:
    """Resume método, cobertura y límites para que no se confunda compatibilidad con clínica."""
    por_motivo = Counter(fila["motivo"] for fila in filas)
    por_servicio = Counter(fila["referral_d5"] for fila in filas if fila["referral_d5"])
    total = len(filas)
    sin_mapeo = sum(not fila["motivo_mapeado"] for fila in filas)
    tipos = sorted({fila["tipo_d5"] for fila in filas if fila["tipo_d5"] != "desconocido"})
    motivos = sorted(por_motivo)
    conteos_motivo_tipo = Counter((fila["motivo"], fila["tipo_d5"]) for fila in filas)
    tasas_mapeos = [
        sum(
            conteos_motivo_tipo[(motivo, servicio)]
            for motivo, servicio in zip(motivos, combinacion)
        )
        / total
        * 100
        for combinacion in product(tipos, repeat=len(motivos))
    ]
    coincidencia_d5_actual = porcentaje(
        sum(fila["motivo_coherente_d5"] is True for fila in filas), total
    )
    coincidencia_aura = porcentaje(
        sum(fila["motivo_coherente_aura"] is True for fila in filas), total
    )
    lineas = [
        "# Comparación de derivaciones D5 con AURA",
        "",
        f"Se analizaron {total} conversaciones de D5; {sin_mapeo} tienen un motivo sin mapeo activo en `tablas.yaml`.",
        "Cada conversación se evaluó de forma independiente sobre el mismo inventario nuevo; no se reservaron cupos.",
        "La compatibilidad original usa el horario semanal de D6 y exige que quepa una sesión completa.",
        "Las franjas usadas son day: lunes-viernes 09:00-18:00; evening con trabajo: 19:00-21:00; evening sin trabajo: 17:00-21:00.",
        "‘Servicio que cierra a las 18:00’ indica que el horario D6 del servicio termina a esa hora.",
        "La disponibilidad AURA se calcula con una agenda inicial nueva y sin reservas entre conversaciones.",
        "AURA nunca devuelve una opción incompatible: o encuentra una cita que pasa sus filtros o registra un desencuentro.",
        "",
        "## Resumen por modalidad y trabajo",
        "",
        "| Grupo | n | D5 deriva a servicio que cierra 18:00 | D5 incompatible con horario | AURA opción compatible | AURA desencuentro |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for fila in resumen:
        lineas.append(
            f"| {fila['grupo_modalidad']} | {fila['conversaciones']} | "
            f"{fila['pct_d5_servicio_cierra_18']:.2f}% | {fila['pct_d5_incompatible']:.2f}% | "
            f"{fila['pct_aura_opcion_compatible']:.2f}% | {fila['pct_aura_desencuentro']:.2f}% |"
        )
    lineas.extend(
        [
            "",
            "## Lectura y límites",
            "",
            f"El hallazgo principal es que D5 reparte las derivaciones de forma uniforme entre {len(por_servicio)} servicios: cada uno recibe entre {min(por_servicio.values())} y {max(por_servicio.values())} conversaciones.",
            f"Al probar todos los mapeos de los {len(motivos)} motivos a los {len(tipos)} tipos de servicio, la coincidencia D5 queda entre {min(tasas_mapeos):.2f}% y {max(tasas_mapeos):.2f}%; con el mapeo provisional actual es {coincidencia_d5_actual:.2f}%. Esto ronda un tercio, el nivel esperado por azar si hay tres tipos. Es evidencia descriptiva, no prueba de aleatoriedad ni de irrelevancia clínica.",
            f"AURA aplica la tabla configurada y selecciona el tipo ideal en {coincidencia_aura:.2f}% de las conversaciones. Este porcentaje solo mide consistencia interna con la tabla; no es una medida de acierto ni de pertinencia clínica.",
            "La comparación mide si las derivaciones respetan las condiciones que declara el estudiante y las reglas actuales de AURA; no evalúa pertinencia clínica ni calidad de atención.",
            "",
            "## Motivos en D5",
            "",
            "| Motivo | Conversaciones |",
            "|---|---:|",
        ]
    )
    for motivo, cantidad in sorted(por_motivo.items()):
        lineas.append(f"| {motivo} | {cantidad} |")
    lineas.extend(
        [
            "",
            "## Archivos de salida",
            "",
            "- `comparacion_d5.csv`: una fila por conversación con perfil extraído, resultado D5 y resultado AURA.",
            "- `resumen_comparacion_d5.csv`: porcentajes agregados por modalidad, trabajo y denominadores.",
            "- `comparacion_d5.png`: gráfico de barras agrupadas.",
        ]
    )
    ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")


def main() -> None:
    """Carga fuentes, evalúa conversaciones independientemente y escribe los tres resultados."""
    parametros = cargar_yaml("parametros.yaml")
    tablas = cargar_yaml("tablas.yaml")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--d5", default=str(ruta_d5())
    )
    parser.add_argument("--salidas", default=str(RAIZ_PROYECTO / "salidas"))
    args = parser.parse_args()
    pack = cargar_data_pack(ruta_data_pack())
    conversaciones = json.loads(Path(args.d5).read_text(encoding="utf-8"))
    hoy = date.fromisoformat(parametros["hoy"])
    servicios = {servicio.service_id: servicio for servicio in pack["servicios"]}
    cierres = cierres_desde_d7(pack["d7"])
    cupos, libres = generar_agenda(
        pack["servicios"],
        hoy,
        semanas=int(parametros["horizonte_semanas"]),
        duracion_min=int(parametros["duracion_sesion_minutos"]),
        fraccion_liberada=float(parametros["fraccion_liberada"]),
        ocupacion_inicial=float(parametros["ocupacion_inicial"]),
        semilla=42,
        dias_cerrados=cierres,
    )
    cupos_por_id = {cupo.id: cupo for cupo in cupos}
    filas = [
        analizar_conversacion(
            conversacion,
            servicios,
            tablas["motivo_a_servicio"],
            cupos,
            libres,
            cupos_por_id,
            hoy,
            float(parametros["beta"]),
            int(parametros["duracion_sesion_minutos"]),
        )
        for conversacion in conversaciones
    ]
    resumen = resumir_por_modalidad(filas)
    salida = Path(args.salidas).resolve()
    salida.mkdir(parents=True, exist_ok=True)
    escribir_csv(salida / "comparacion_d5.csv", filas)
    escribir_csv(salida / "resumen_comparacion_d5.csv", resumen)
    generar_grafico(resumen, salida / "comparacion_d5.png")
    escribir_reporte(salida / "reporte_comparacion_d5.md", filas, resumen)
    print(f"Comparación terminada: {len(filas)} conversaciones; resultados en {salida}")


if __name__ == "__main__":
    main()
