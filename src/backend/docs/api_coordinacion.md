# API de Coordinación

Contrato para el frontend. Todo el JSON está en **snake_case** y las etiquetas en español ya vienen en la respuesta
(`*_label`): el front no traduce códigos. Los ejemplos son respuestas reales de la demo (se recortan las listas largas;
el tamaño real se indica en cada caso). Prefijo común: `/api`. Esquemas completos: `/docs` (Swagger) con el servidor corriendo.

## Conceptos

- **Estado único en RAM.** Una reserva o un desencuentro hecho desde la vista del estudiante aparece en estos endpoints
  sin reiniciar. `POST /api/demo/reiniciar` vuelve al estado sembrado.
- **Todo es simulación.** La demanda se simula con el motor (escenario y semilla en `parametros.yaml`, bloque `demo`);
  mostrar siempre `etiqueta` de `/api/demo/estado` en la cabecera del panel.
- **Fechas de la demo.** Los pedidos simulados se fechan dentro de la semana de evaluaciones de D7 (lunes 9 a domingo 15 de
  noviembre de 2026), conservando el día de la semana que trae D2. `hoy` es el último día de esa semana (domingo 15), así que todo lo
  sembrado queda en el pasado o en hoy.
- **Ventana de cada pedido.** Cada pedido se procesa en orden de llegada y solo ve cupos de **su fecha de solicitud + 1 hasta su fecha + 14 días**
  (`7 × horizonte_semanas`); ningún pedido toma un cupo fuera de esa ventana. Los pedidos en vivo del estudiante usan `hoy` como fecha
  de solicitud, así que ven de hoy + 1 a hoy + 14.
- **Agenda** (`agenda_inicio`–`agenda_fin`): todo lo generado, del día siguiente al primer pedido (10 nov) hasta `hoy` + horizonte (29 nov).
  **Agenda abierta** (`agenda_abierta_inicio`–`agenda_abierta_fin`): lo que todavía se puede reservar, de `hoy` + 1 (16 nov) al fin de la agenda.
  La capacidad semanal de D6 se reparte por semana calendario (Lun–Dom); una semana cortada por el inicio o el fin de la agenda recibe capacidad
  proporcional a los días de atención del servicio que caen dentro del rango.
- **Embudo de cupos** (por servicio y de toda la red, sobre la agenda abierta): `capacidad_agenda_abierta` (la capacidad semanal de D6 prorrateada a
  los días de la agenda abierta) → `libres_agenda_abierta` (después de la ocupación inicial del servicio) → `cupos_liberados` (la parte de los libres que
  el servicio presta a AURA) → `cupos_reservados` (los que AURA ya asignó a un estudiante). `capacidad_semanal` es la de D6, sin prorratear.
  `/api/demo/estado` trae los porcentajes (`ocupacion_inicial_pct`, `fraccion_liberada_pct`), `agenda_abierta_semanas`, el rango de pedidos y la línea
  base de espera para que el front arme sus textos sin escribir cifras a mano.
- **Qué mide cada KPI**
  - `cupos_liberados`, `cupos_reservados` y `ocupacion_pct` se calculan **solo sobre la agenda abierta**: los cupos libres de días ya pasados
    no se pueden usar y no cuentan como liberados. Ocupación = `cupos_reservados / cupos_liberados × 100`, sobre cupos **liberados** (no sobre la capacidad total).
  - `citas_agendadas`, `espera_media_dias` y `desencuentros` cuentan **todo lo sembrado** en la semana de pedidos (9–15 nov), incluidas las citas
    que cayeron en días ya pasados; por eso `citas_agendadas` puede ser mayor que `cupos_reservados`.
  - Con `?semana=YYYY-MM-DD` los cupos se acotan a esa semana Lun–Dom dentro de la agenda abierta (una semana pasada da 0 liberados) y las citas a las solicitadas esa semana.
- **Atendidos con alternativa afín** (`kpis.atendidos_alternativa`, `demanda_por_tipo`): pedidos cuyo servicio ideal era de un tipo y que
  terminaron en un cupo de **otro tipo** porque la afinidad lo permite. `demanda_por_tipo` desglosa, por tipo ideal, los `pedidos`
  (atendidos + sin cupo), los `atendidos_en_su_tipo`, los `atendidos_con_alternativa` (y a qué tipo se desviaron, en `destinos`) y los `sin_cupo`.
  Así se ve la demanda real de un tipo (p. ej. Consejería) aunque la ocupación de sus servicios parezca media. En el detalle de un servicio,
  `demanda_del_tipo` es la fila de su tipo (toda la demanda del tipo, no solo la de ese local) y `recibidos_como_alternativa` cuenta las citas
  de ese servicio cuyo pedido pedía otro tipo. Solo cuentan citas que conocen su servicio ideal: todas las sembradas y las reservas en vivo
  que envíen `servicio_ideal` (el de la propuesta).
- **Nivel:** `baja` < 50, `media` 50–70, `alta` > 70 (`coordinacion.nivel_ocupacion`). `alta_demanda` = nivel `alta`.
- **Espera** = `fecha_cupo − fecha_solicitud`, en días: la misma definición que `wait_days` en D2, así la comparación con la línea base es justa.
  `espera_media_dias` es la media sobre todas las citas sembradas; `espera_linea_base_dias` es la media observada en D2 (≈ 41,96).
- **Grupo** (`diurno`/`nocturno`) es el que trae la solicitud; la franja se muestra tal cual. El front no debe deducir el grupo por la hora.
- Un **servicio** se muestra siempre como nombre de D6 + `tipo_label` (p. ej. «Espacio Brújula Orientación · Consejería»).
  Los nombres de D6 pueden confundirse con orientación vocacional.
- **Errores:** `{"error": "<codigo>", "detalle": "..."}` (404 `no_encontrado`, 409 `cupo_ya_tomado`, 422 `solicitud_invalida` —también al reservar un cupo fuera de la ventana hoy + 1 … hoy + 14—;
  los errores de validación de parámetros usan el formato estándar de FastAPI).

## Tabla de endpoints

| Método | Ruta | Para qué |
|---|---|---|
| GET | `/api/salud` | Salud del servicio |
| GET | `/api/demo/estado` | Fecha demo, semana, rango de la agenda y de la agenda abierta, y etiqueta del escenario |
| POST | `/api/demo/reiniciar` | Reconstruye y vuelve a sembrar la demo |
| GET | `/api/coordinacion/resumen?semana=` | KPI y ocupación por servicio |
| GET | `/api/coordinacion/servicios?tipo=&canal=&distrito=&nivel=&solo_alta_demanda=&semana=` | GeoJSON de servicios para el mapa |
| GET | `/api/coordinacion/servicios/{service_id}?semana=` | Detalle de un servicio |
| GET | `/api/coordinacion/desencuentros?motivo=&distrito=&servicio_ideal=&grupo=&pagina=&tamano=` | Tabla, matriz distrito × servicio, franja principal e insight |
| GET | `/api/coordinacion/desencuentros.csv` | Los mismos filtros, sin paginar |
| GET | `/api/coordinacion/lotes` | Modo lote: servicios por utilización, lote abierto con cuenta regresiva e historial |
| GET | `/api/coordinacion/actividad?desde=&limite=` | Registro de lo **nuevo** (citas reservadas o canceladas y desencuentros hechos después de arrancar la demo) |
| GET | `/api/coordinacion/actividad/stream?desde=` | Lo mismo en **tiempo real** (Server-Sent Events) |
| GET | `/api/coordinacion/reglas` | Reglas del motor en solo lectura |

## GET /api/demo/estado

```json
{
  "hoy": "2026-11-15",
  "semana_inicio": "2026-11-09",
  "semana_fin": "2026-11-15",
  "agenda_inicio": "2026-11-10",
  "agenda_fin": "2026-11-29",
  "agenda_abierta_inicio": "2026-11-16",
  "agenda_abierta_fin": "2026-11-29",
  "escenario": "x6",
  "etiqueta": "Simulación · escenario de estrés en semana de evaluaciones (demanda ×6) · 10 % vespertinos que trabajan",
  "semilla": 42,
  "factor_demanda": 6.0,
  "proporcion_vespertino_trabaja": 0.1,
  "pedidos_desde": "2026-11-09",
  "pedidos_hasta": "2026-11-15",
  "agenda_abierta_semanas": 2,
  "ocupacion_inicial_pct": 10.0,
  "fraccion_liberada_pct": 50.0,
  "espera_linea_base_dias": 41.96,
  "umbrales_nivel": {
    "baja_menor_que": 50.0,
    "alta_mayor_que": 70.0
  }
}
```

Cabecera: `etiqueta`. Panel: «Agenda abierta: del {agenda_abierta_inicio} al {agenda_abierta_fin}». `semana_inicio`/`semana_fin` son
el lunes y el domingo de la semana de `hoy` (la de los pedidos); `agenda_inicio`/`agenda_fin` son todo lo generado.

## POST /api/demo/reiniciar

Devuelve lo mismo que `/api/demo/estado`. Tras la llamada, recargar todos los datos del panel.

```json
{
  "hoy": "2026-11-15",
  "semana_inicio": "2026-11-09",
  "semana_fin": "2026-11-15",
  "agenda_inicio": "2026-11-10",
  "agenda_fin": "2026-11-29",
  "agenda_abierta_inicio": "2026-11-16",
  "agenda_abierta_fin": "2026-11-29",
  "escenario": "x6",
  "etiqueta": "Simulación · escenario de estrés en semana de evaluaciones (demanda ×6) · 10 % vespertinos que trabajan",
  "semilla": 42,
  "factor_demanda": 6.0,
  "proporcion_vespertino_trabaja": 0.1,
  "pedidos_desde": "2026-11-09",
  "pedidos_hasta": "2026-11-15",
  "agenda_abierta_semanas": 2,
  "ocupacion_inicial_pct": 10.0,
  "fraccion_liberada_pct": 50.0,
  "espera_linea_base_dias": 41.96,
  "umbrales_nivel": {
    "baja_menor_que": 50.0,
    "alta_mayor_que": 70.0
  }
}
```

## GET /api/coordinacion/resumen

`agenda_abierta` es el rango sobre el que se miden el embudo de cupos (`capacidad_agenda_abierta`, `libres_agenda_abierta`, `cupos_liberados`, `cupos_reservados`) y `ocupacion_pct`; `pedidos` es el rango de pedidos que cuentan
`citas_agendadas` y `espera_media_dias` (con `?semana=` ambos se acotan a esa semana). `servicios` trae los 15 servicios (aquí se muestran 2).

```json
{
  "agenda_abierta": {
    "desde": "2026-11-16",
    "hasta": "2026-11-29"
  },
  "pedidos": {
    "desde": "2026-11-09",
    "hasta": "2026-11-15"
  },
  "kpis": {
    "citas_agendadas": 762,
    "espera_media_dias": 4.5,
    "espera_linea_base_dias": 41.96,
    "capacidad_agenda_abierta": 2310,
    "libres_agenda_abierta": 2076,
    "cupos_liberados": 1036,
    "cupos_reservados": 483,
    "ocupacion_pct": 46.6,
    "desencuentros": 38,
    "atendidos_alternativa": 180
  },
  "demanda_por_tipo": [
    {
      "ideal": "counseling",
      "ideal_label": "Consejería",
      "pedidos": 499,
      "atendidos_en_su_tipo": 314,
      "atendidos_con_alternativa": 164,
      "sin_cupo": 21,
      "destinos": [
        {
          "tipo": "peer_support",
          "tipo_label": "Apoyo entre pares",
          "cantidad": 164
        }
      ]
    },
    {
      "ideal": "peer_support",
      "ideal_label": "Apoyo entre pares",
      "pedidos": 197,
      "atendidos_en_su_tipo": 172,
      "atendidos_con_alternativa": 16,
      "sin_cupo": 9,
      "destinos": [
        {
          "tipo": "counseling",
          "tipo_label": "Consejería",
          "cantidad": 16
        }
      ]
    },
    {
      "ideal": "career_guidance",
      "ideal_label": "Orientación vocacional",
      "pedidos": 104,
      "atendidos_en_su_tipo": 96,
      "atendidos_con_alternativa": 0,
      "sin_cupo": 8,
      "destinos": []
    }
  ],
  "servicios": [
    {
      "service_id": "SRV_AE_001",
      "nombre": "Espacio Brújula Orientación",
      "tipo": "counseling",
      "tipo_label": "Consejería",
      "ocupacion_pct": 71.1,
      "nivel": "alta",
      "capacidad_semanal": 42,
      "capacidad_agenda_abierta": 84,
      "libres_agenda_abierta": 76,
      "cupos_liberados": 38,
      "cupos_reservados": 27
    },
    {
      "service_id": "SRV_AE_002",
      "nombre": "Espacio Brújula Pares",
      "tipo": "peer_support",
      "tipo_label": "Apoyo entre pares",
      "ocupacion_pct": 77.1,
      "nivel": "alta",
      "capacidad_semanal": 55,
      "capacidad_agenda_abierta": 110,
      "libres_agenda_abierta": 98,
      "cupos_liberados": 48,
      "cupos_reservados": 37
    }
  ]
}
```

## GET /api/coordinacion/servicios

GeoJSON `FeatureCollection` con la geometría de D6 tal cual. Filtros: `tipo` (`counseling`, `peer_support`, `career_guidance`),
`canal` (`digital`, `phone`, `in_person`), `solo_alta_demanda=true`. Sin filtros hay 15 servicios (se muestra 1). Con la configuración actual `solo_alta_demanda=true` devuelve 6: si la lista queda vacía, el mapa debe mostrar un estado vacío.

- `properties.pos`: `x`, `y` entre 0 y 1 según el bounding box de los 15 puntos. `x` crece hacia el este y **`y` crece hacia el sur** (0 = norte), listo para posicionar en el mapa ilustrado.
- `direccion` es `null`: D6 no la trae.
- `horario_texto` es para mostrar; `horario` es la versión estructurada.

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "SRV_AE_001",
      "geometry": {
        "type": "Point",
        "coordinates": [-72.5, -18.7]
      },
      "properties": {
        "service_id": "SRV_AE_001",
        "nombre": "Espacio Brújula Orientación",
        "tipo": "counseling",
        "tipo_label": "Consejería",
        "distrito": "DIST_GAIA",
        "direccion": null,
        "horario_texto": "Lun–Vie · 09:00–18:00",
        "horario": [
          {
            "dias": ["Lun", "Mar", "Mié", "Jue", "Vie"],
            "desde": "09:00",
            "hasta": "18:00"
          }
        ],
        "canales": ["in_person", "digital"],
        "canales_label": ["Presencial", "Videollamada"],
        "capacidad_semanal": 42,
        "capacidad_agenda_abierta": 84,
        "libres_agenda_abierta": 76,
        "cupos_liberados": 38,
        "cupos_reservados": 27,
        "ocupacion_pct": 71.1,
        "nivel": "alta",
        "alta_demanda": true,
        "eligibility": "Aethera students; fictional orientation service",
        "referral_information": "student_id, preferred channel, non-clinical reason code",
        "pos": {
          "x": 0.0,
          "y": 1.0
        }
      }
    }
  ]
}
```

## GET /api/coordinacion/servicios/{service_id}

`servicio` repite las propiedades de GeoJSON. `cupos_por_dia` cubre toda la agenda (`abierto` indica si el día todavía se puede reservar) (14 días con cupos).
`desencuentros_recientes` son los más recientes cuyo `servicio_ideal` es del mismo tipo y cuyo `distrito` es el del servicio (máximo 5). 404 si no existe.

```json
{
  "servicio": "… (mismas propiedades que en GeoJSON)",
  "demanda_del_tipo": {
    "ideal": "counseling",
    "ideal_label": "Consejería",
    "pedidos": 499,
    "atendidos_en_su_tipo": 314,
    "atendidos_con_alternativa": 164,
    "sin_cupo": 21,
    "destinos": [
      {
        "tipo": "peer_support",
        "tipo_label": "Apoyo entre pares",
        "cantidad": 164
      }
    ]
  },
  "recibidos_como_alternativa": {
    "cantidad": 7,
    "origenes": [
      {
        "tipo": "peer_support",
        "tipo_label": "Apoyo entre pares",
        "cantidad": 7
      }
    ]
  },
  "cupos_por_dia": [
    {
      "fecha": "2026-11-10",
      "dia": "Mar",
      "capacidad": 9,
      "libres": 8,
      "liberados": 3,
      "reservados": 3,
      "abierto": false
    },
    {
      "fecha": "2026-11-11",
      "dia": "Mié",
      "capacidad": 9,
      "libres": 9,
      "liberados": 7,
      "reservados": 7,
      "abierto": false
    },
    {
      "fecha": "2026-11-12",
      "dia": "Jue",
      "capacidad": 9,
      "libres": 7,
      "liberados": 4,
      "reservados": 4,
      "abierto": false
    }
  ],
  "desencuentros_recientes": [
    {
      "id": "DES-0000036",
      "fecha": "2026-11-13",
      "motivo": "academic_pressure",
      "motivo_label": "Presión académica",
      "servicio_ideal": "counseling",
      "servicio_ideal_label": "Consejería",
      "distrito": "DIST_GAIA",
      "franja": {
        "dia": "Lun–Vie",
        "desde": "19:00",
        "hasta": "21:00"
      },
      "canales_aceptables": ["digital", "phone", "in_person"],
      "canales_label": ["Videollamada", "Teléfono", "Presencial"],
      "grupo": "nocturno",
      "grupo_label": "Nocturno"
    }
  ]
}
```

## GET /api/coordinacion/desencuentros

`total` = todos los registrados; `filtrados` = tras los filtros; `paginas` ≥ 1. Orden: más recientes primero. La **matriz**, la **franja principal** y `insight_filtro` se calculan sobre el conjunto filtrado (no solo la página); `insight` no.

- **`matriz_distrito_servicio`:** conteo de desencuentros por distrito (filas, los de D6) y servicio ideal (columnas, los tipos), con `total_filas`, `total_columnas` y `total`. Respeta los filtros; en el front, un clic en una celda aplica sus dos filtros.
- **`franja_principal`:** `{texto, porcentaje, desde, hasta, dias}`; la franja (horas y días) que más declaran los pedidos del conjunto, p. ej. «100 % piden entre 19:00 y 21:00, lunes a viernes». `null` si no hay desencuentros. Todos los desencuentros simulados declaran la misma franja.
- **`insight`:** el hallazgo principal, siempre sobre **todos** los desencuentros (no cambia con los filtros): la combinación (grupo, servicio ideal, franja) más frecuente, redactada en español. **`insight_filtro`** es el mismo cálculo sobre el conjunto filtrado (`null` si no hay filtros activos): el front lo muestra debajo como «En este filtro: …».
- `franja` (en cada ítem) resume el primer tramo horario de la solicitud, con sus días agrupados (`Lun–Vie`).

Ejemplo con `tamano=2&grupo=nocturno` (se muestra 1 ítem y 2 filas de la matriz):

```json
{
  "total": 38,
  "filtrados": 38,
  "pagina": 1,
  "paginas": 19,
  "items": [
    {
      "id": "DES-0000038",
      "fecha": "2026-11-13",
      "motivo": "sleep_and_routine",
      "motivo_label": "Sueño y rutina",
      "servicio_ideal": "counseling",
      "servicio_ideal_label": "Consejería",
      "distrito": "DIST_HORIZON",
      "franja": {
        "dia": "Lun–Vie",
        "desde": "19:00",
        "hasta": "21:00"
      },
      "canales_aceptables": ["digital", "phone", "in_person"],
      "canales_label": ["Videollamada", "Teléfono", "Presencial"],
      "grupo": "nocturno",
      "grupo_label": "Nocturno"
    }
  ],
  "matriz_distrito_servicio": {
    "distritos": ["DIST_GAIA", "DIST_HORIZON"],
    "servicios": [
      {
        "tipo": "counseling",
        "label": "Consejería"
      },
      {
        "tipo": "peer_support",
        "label": "Apoyo entre pares"
      },
      {
        "tipo": "career_guidance",
        "label": "Orientación vocacional"
      }
    ],
    "celdas": [
      [4, 3, 4],
      [6, 2, 1]
    ],
    "total_filas": [11, 9],
    "total_columnas": [21, 9, 8],
    "total": 38
  },
  "franja_principal": {
    "texto": "entre 19:00 y 21:00, lunes a viernes",
    "porcentaje": 100.0,
    "desde": "19:00",
    "hasta": "21:00",
    "dias": "lunes a viernes"
  },
  "insight": {
    "texto": "55,3 % de los desencuentros son de estudiantes nocturnos que buscan consejería entre las 19:00 y las 21:00.",
    "porcentaje": 55.3,
    "grupo": "nocturno",
    "servicio_ideal": "counseling",
    "franja": {
      "dia": "Lun–Vie",
      "desde": "19:00",
      "hasta": "21:00"
    }
  },
  "insight_filtro": {
    "texto": "55,3 % de los desencuentros son de estudiantes nocturnos que buscan consejería entre las 19:00 y las 21:00.",
    "porcentaje": 55.3,
    "grupo": "nocturno",
    "servicio_ideal": "counseling",
    "franja": {
      "dia": "Lun–Vie",
      "desde": "19:00",
      "hasta": "21:00"
    }
  }
}
```

**Estado vacío.** Un filtro sin resultados (aquí `grupo=diurno`) devuelve `filtrados: 0`, `items: []` y un insight con texto explicativo;
el front debe mostrar un mensaje, no una tabla en blanco:

```json
{
  "total": 38,
  "filtrados": 0,
  "pagina": 1,
  "paginas": 1,
  "items": [],
  "insight": {
    "texto": "55,3 % de los desencuentros son de estudiantes nocturnos que buscan consejería entre las 19:00 y las 21:00.",
    "porcentaje": 55.3,
    "grupo": "nocturno",
    "servicio_ideal": "counseling",
    "franja": {
      "dia": "Lun–Vie",
      "desde": "19:00",
      "hasta": "21:00"
    }
  }
}
```

## GET /api/coordinacion/desencuentros.csv

Mismos filtros; sin paginar. Adjunto `desencuentros.csv`, UTF-8 con BOM (Excel). Primeras líneas:

```csv
id,fecha,motivo,motivo_label,servicio_ideal,servicio_ideal_label,distrito,franja_dia,franja_desde,franja_hasta,canales_aceptables,grupo
DES-0000038,2026-11-13,sleep_and_routine,Sueño y rutina,counseling,Consejería,DIST_HORIZON,Lun–Vie,19:00,21:00,digital;phone;in_person,nocturno
DES-0000037,2026-11-13,social_support,Apoyo social,peer_support,Apoyo entre pares,DIST_GAIA,Lun–Vie,19:00,21:00,digital;phone;in_person,nocturno
```

## GET /api/coordinacion/reglas

Cinco bloques en solo lectura; los valores técnicos de los datos llegan traducidos (`umbral_texto`: «media o alta»; `umbral` conserva el valor de la configuración); cada uno trae `provisional` (leído de `tablas.yaml`). Ejemplo recortado:

```json
{
  "motivo_servicio": {
    "provisional": true,
    "items": [
      {
        "motivo": "academic_pressure",
        "motivo_label": "Presión académica",
        "servicio": "counseling",
        "servicio_label": "Consejería"
      },
      {
        "motivo": "sleep_and_routine",
        "motivo_label": "Sueño y rutina",
        "servicio": "counseling",
        "servicio_label": "Consejería"
      }
    ]
  },
  "afinidad": {
    "provisional": true,
    "minimo_alternativa": 0.5,
    "minimo_provisional": true,
    "tipos": [
      {
        "codigo": "counseling",
        "label": "Consejería"
      },
      {
        "codigo": "peer_support",
        "label": "Apoyo entre pares"
      },
      {
        "codigo": "career_guidance",
        "label": "Orientación vocacional"
      }
    ],
    "matriz": [
      {
        "ideal": "counseling",
        "ideal_label": "Consejería",
        "valores": [
          {
            "tipo": "counseling",
            "tipo_label": "Consejería",
            "valor": 1.0
          },
          {
            "tipo": "peer_support",
            "tipo_label": "Apoyo entre pares",
            "valor": 0.6
          },
          {
            "tipo": "career_guidance",
            "tipo_label": "Orientación vocacional",
            "valor": 0.3
          }
        ]
      }
    ]
  },
  "aviso": {
    "provisional": false,
    "puntaje_minimo": 3,
    "solo_semanas_evaluacion": true,
    "evento_evaluacion": "evaluation_week",
    "senales": [
      {
        "id": "S1",
        "nombre": "Alerta de abandono",
        "descripcion": "La alerta de abandono es media o alta.",
        "umbral": ["medium", "high"],
        "umbral_texto": "media o alta"
      },
      {
        "id": "S2",
        "nombre": "Caída de asistencia",
        "descripcion": "La tasa de asistencia bajó al menos 0,05 frente al período anterior.",
        "umbral": 0.05,
        "umbral_texto": "0,05"
      }
    ]
  },
  "p_asistencia": {
    "provisional": false,
    "canales": [
      {
        "canal": "digital",
        "canal_label": "Videollamada",
        "valor": 0.725
      },
      {
        "canal": "phone",
        "canal_label": "Teléfono",
        "valor": 0.707
      },
      {
        "canal": "in_person",
        "canal_label": "Presencial",
        "valor": 0.667
      }
    ]
  },
  "pesos": {
    "provisional": true,
    "terminos": [
      {
        "id": "Z1",
        "nombre": "Estudiantes sin cita",
        "peso": 0.35
      },
      {
        "id": "Z2",
        "nombre": "Espera ajustada por canal",
        "peso": 0.25
      }
    ]
  }
}
```

## Vista del estudiante (mismo estado)

Se usan en la etapa siguiente. **Cambio:** estos endpoints devuelven y reciben **snake_case** (antes camelCase); si el front del estudiante los consume, hay que adaptarlo.

| Método | Ruta | Para qué |
|---|---|---|
| GET | `/api/services` | Servicios de la red (con `tipo_label`) |
| GET | `/api/services/{service_id}/slots` | Cupos libres de un servicio |
| POST | `/api/appointments/proposals?k=3` | Opciones compatibles (no reserva) |
| POST | `/api/appointments` | Reserva `{estudiante_id, opcion_id, servicio_ideal?}`; 409 si el cupo ya fue tomado |
| GET | `/api/appointments?estudiante_id=` | Citas del estudiante |
| DELETE | `/api/appointments/{cita_id}` | Cancela y libera el cupo |

`POST /api/appointments/proposals` con el cuerpo:

```json
{
  "estudiante_id": "STU_DEMO_001",
  "motivo": "social_support",
  "distrito": "DIST_GAIA",
  "grupo": "diurno",
  "franjas": [
    {
      "dia": "Mon",
      "desde": "09:00",
      "hasta": "18:00"
    },
    {
      "dia": "Tue",
      "desde": "09:00",
      "hasta": "18:00"
    },
    {
      "dia": "Wed",
      "desde": "09:00",
      "hasta": "18:00"
    }
  ],
  "canales_aceptables": ["digital", "phone"]
}
```

responde (k=1):

```json
{
  "opciones": [
    {
      "opcion_id": "C0002328|phone",
      "service_id": "SRV_AE_005",
      "servicio_nombre": "Espacio Lumen Pares",
      "tipo": "peer_support",
      "tipo_label": "Apoyo entre pares",
      "distrito": "DIST_NEBULA",
      "fecha": "2026-11-24",
      "hora_inicio": "13:00",
      "hora_fin": "14:00",
      "canal": "phone",
      "dias_espera": 9,
      "es_alternativa": false,
      "afinidad": 1.0
    }
  ],
  "servicio_ideal": "peer_support",
  "motivo_vacio": null
}
```

`POST /api/appointments` con `{"estudiante_id": "STU_DEMO_001", "opcion_id": "C0002328|phone"}` responde 201:

```json
{
  "id": "CITA-0000763",
  "estudiante_id": "STU_DEMO_001",
  "service_id": "SRV_AE_005",
  "servicio_nombre": "Espacio Lumen Pares",
  "tipo_label": "Apoyo entre pares",
  "slot": {
    "id": "C0002328",
    "service_id": "SRV_AE_005",
    "fecha_iso": "2026-11-24T13:00:00",
    "disponible": false,
    "canales": ["phone"]
  },
  "canal": "phone",
  "estado": "confirmada"
}
```

Un segundo intento sobre la misma opción responde 409 `{   "error": "cupo_ya_tomado",   "detalle": "C0002328|phone" }`.
`GET /api/services/{service_id}/slots` devuelve 11 cupos libres para el primer servicio; cada uno: `{   "id": "C0002110",   "service_id": "SRV_AE_001",   "fecha_iso": "2026-11-25T09:00:00",   "disponible": true,   "canales": ["in_person", "digital"] }`
(la opción a reservar es `<id>|<canal>`).

## Notas para el frontend (Fase E)

- Mostrar `etiqueta` de `/api/demo/estado` visible en la cabecera: la demo es simulación, no dato observado.
- Mostrar «Agenda abierta: del X al Y» con `agenda_abierta_inicio`/`agenda_abierta_fin`.
- Si ningún servicio está en nivel `alta`, el filtro «solo alta demanda» devuelve una lista vacía: mostrar un estado vacío en el mapa.
- Franja y grupo: tal como vienen; nunca deducir el grupo por la hora.
- Servicio = nombre de D6 + `tipo_label`, en todas las vistas (tarjetas, tabla, mapa, tooltip, detalle).
- Desencuentros: si un filtro deja la tabla vacía, estado vacío con mensaje explicativo (usar `insight.texto`).
- Resumen: KPI «Atendidos con alternativa afín» y tabla «Demanda real por tipo de servicio» (`demanda_por_tipo`); detalle del servicio: bloque «Demanda de {tipo}».
- Los textos de los ⓘ viven en `lib/glosario.ts` y se rellenan con `/api/demo/estado`; el embudo de cupos usa los 4 campos por servicio.
- Reinicio: botón «Reiniciar demo» → `POST /api/demo/reiniciar` y recargar.
- Los endpoints del estudiante pasaron a snake_case.


## Actividad en vivo

Para mostrar en pantalla, al mismo tiempo, lo que hace un estudiante y lo que ve Coordinación. **Solo registra lo nuevo**: lo que llega por la API de citas o por el chat después de arrancar. Las citas y desencuentros sembrados de la demo no aparecen. Todo vive en RAM: reiniciar el backend o la demo vacía el registro.

`GET /api/coordinacion/actividad?desde=0&limite=200` → `{ "epoca", "ultimo_id", "eventos": [...] }`, del más antiguo al más reciente. `desde` devuelve solo los eventos con id mayor.

Cada evento:

| Campo | Descripción |
|---|---|
| `id` | Entero creciente; sirve como cursor |
| `tipo` | `cita_reservada`, `cita_cancelada`, `desencuentro`, `servicio_en_lote` / `servicio_sale_de_lote` (un servicio cruzó el umbral), `lote_abierto`, `lote_solicitud` o `lote_resuelto` |
| `registrado_en` | Instante real del registro (ISO, UTC) |
| `fecha_solicitud` | Fecha **simulada** de la demo en que ocurrió (`hoy`) |
| `origen` | `chat` (agente AURA), `api` o `lote` (citas que asigna un lote) |
| `estudiante_id` | Quién (null en eventos del sistema: umbral, lote resuelto) |
| `servicio` | `{service_id, nombre, tipo, tipo_label, distrito}` (null en desencuentros) |
| `ocupacion` | `{pct, antes_pct, reservados, liberados, nivel, en_lote}` del servicio **tras** el evento: cupos reservados / liberados de la agenda abierta (null en desencuentros) |
| `cita` | `{cita_id, fecha, hora_inicio, hora_fin, canal, canal_label, dias_espera, es_alternativa}` (null en desencuentros) |
| `lote` | `{id, estado, solicitudes, tamano_maximo, ventana_s, cierra_en, resultado}` (eventos de lote; `resultado` solo al resolverse) |
| `umbral_pct` | Umbral de modo lote (solo en `servicio_en_lote` / `servicio_sale_de_lote`) |
| `desencuentro` | `{registro_id, motivo, motivo_label, servicio_ideal, servicio_ideal_label, distrito, grupo, grupo_label, franjas, canales}` (solo desencuentros) |

`GET /api/coordinacion/actividad/stream?desde=<ultimo_id>` es un `text/event-stream`:

- `event: inicio` al conectar: `{epoca, ultimo_id, reinicio}` (`reinicio: true` si el cliente venía de otra ejecución: debe vaciar su lista).
- `event: actividad` (con `id:`) por cada evento nuevo, con el JSON de arriba.
- `event: reinicio` si se reinicia la demo con el flujo abierto.
- Un comentario `: ping` cada 15 s para mantener la conexión.

`EventSource` reconecta solo y reenvía `Last-Event-ID`; el servidor no repite lo ya entregado. El frontend (`components/coordinacion/ActividadProvider.tsx`) carga primero `GET /actividad` y luego abre el flujo con `desde=ultimo_id`.


## Modo lote

`GET /api/coordinacion/lotes` → todo lo que muestra la pantalla **Lotes**. Reglas completas: [como_funciona.md §8](como_funciona.md).

| Campo | Descripción |
|---|---|
| `umbral_pct`, `ventana_s`, `tamano_maximo` | Parámetros del modo lote (75 %, 30 s, 5 por defecto) |
| `servidor_ahora` | Hora del servidor (ISO UTC): la cuenta regresiva se calcula con ella, sin depender del reloj del navegador |
| `servicios[]` | Los 15 servicios, de mayor a menor utilización: `{service_id, nombre, tipo, tipo_label, distrito, pct, reservados, liberados, en_lote}` |
| `abierto` | El lote que espera solicitudes (o `null`): `{id, estado, abierto_en, cierra_en, solicitudes[], resultado: null}` |
| `historial[]` | Lotes resueltos, el más reciente primero. `resultado`: `{asignados, sin_cupo, tiempo_s, poblacion, generaciones, genetico, llegada, mejora_sobre_llegada, asignaciones[], sin_cupo_estudiantes[]}` |

`resultado.genetico` y `resultado.llegada` traen las mismas métricas (`objetivo`, `asignados`, `desencuentros`, `espera_media`, `espera_diurnos`, `espera_nocturnos`, `z`) para el mismo grupo asignado con el genético y por orden de llegada. Cada `asignaciones[]` incluye `orden_asignacion` (la prioridad que le dio el genético) y `posicion_llegada`.

El lote se cierra solo; los cambios llegan por el flujo de actividad (`lote_abierto`, `lote_solicitud`, `lote_resuelto`, `servicio_en_lote`): la pantalla vuelve a pedir este endpoint con cada uno.
