# Diccionario de datos — Aethera (Oleada 1)

> Generado a partir de `DATA_DICTIONARY.xlsm`. Datos 100% sintéticos, no clínicos, de uso público.
> Convenciones: **PK** = llave primaria (identifica una fila de forma única). **FK** = llave foránea (apunta a otro archivo).

## Índice

- [Resumen de datasets](#resumen-de-datasets)
- [D1 — Encuesta de bienestar](#d1--encuesta-de-bienestar-d1_wellbeing_surveycsv)
- [D2 — Eventos de servicios de apoyo](#d2--eventos-de-servicios-de-apoyo-d2_support_servicescsv)
- [D3 — Trayectoria académica](#d3--trayectoria-académica-d3_academic_trajectorycsv)
- [D4 — Testimonios (Oleada 2, no incluido aquí)](#d4--testimonios-oleada-2-no-incluido-aquí)
- [D5 — Chats de orientación (Oleada 2, no incluido aquí)](#d5--chats-de-orientación-oleada-2-no-incluido-aquí)
- [D6 — Mapa de servicios](#d6--mapa-de-servicios-d6_services_mapgeojson)
- [D7 — Calendario académico](#d7--calendario-académico-d7_calendarcsv--ics)
- [Relaciones entre datasets](#relaciones-entre-datasets)
- [Métricas de misión (referencia)](#métricas-de-misión-referencia)

---

## Resumen de datasets

| Dataset | Descripción | Formato | Filas | Oleada | Privacidad |
|---|---|---|---|---|---|
| D1 | Encuesta de bienestar | CSV | 12,000 | 1 | PUBLIC |
| D2 | Eventos de servicios de apoyo | CSV | 9,400 | 1 | PUBLIC |
| D3 | Trayectoria académica (formato largo) | CSV | 130,000 | 1 | PUBLIC |
| D4 | Testimonios en primera persona | JSON | 6,000 | 2 | PUBLIC |
| D5 | Chats de orientación no clínicos | JSON | 2,500 | 2 | PUBLIC |
| D6 | Mapa ficticio de servicios | GeoJSON | 15 | 1 | PUBLIC |
| D7 | Calendario académico ficticio | CSV + ICS | 1 año | 1 | PUBLIC |

---

## D1 — Encuesta de bienestar (`D1_wellbeing_survey.csv`)

**Llave:** `student_id` (PK, 1 fila por estudiante, sin duplicados).

| Campo | Tipo | Valores / rango | Nullable | Descripción |
|---|---|---|---|---|
| student_id | string | — | No | Identificador sintético del estudiante. **PK.** FK usada por D2 y D3. |
| survey_date | date | — | No | Fecha de respuesta de la encuesta |
| institution_id | enum | UNI_NOVA_AETHER \| INST_NEXUS \| UNI_HORIZONTE | No | Institución |
| district_id | enum | DIST_GAIA \| DIST_NEBULA \| DIST_VECTOR \| DIST_HORIZON \| DIST_QUANTUM | No | Distrito ficticio |
| country_context | enum | Chile \| Peru | No | Contexto país sintético |
| migration_status | enum | local \| internal_migrant | No | Si el perfil migró internamente |
| study_mode | enum | day \| evening | No | Turno de estudio |
| academic_stage | enum | early \| middle \| final | No | Etapa académica sintética |
| employment_status | enum | not_working \| part_time \| full_time | No | Situación laboral |
| work_hours_week | integer | 0–45 | No | Horas de trabajo semanales |
| sleep_hours | float | 3.5–9.5 | No | Horas de sueño típicas |
| anxiety_score | integer | 0–21 | No | Puntaje sintético de ansiedad (**no diagnóstico**) |
| anxiety_band | enum | low \| mild \| moderate \| high | No | Categoría del puntaje de ansiedad |
| stress_score | integer | 0–24 | No | Puntaje sintético de estrés (**no diagnóstico**) |
| stress_band | enum | low \| moderate \| high | No | Categoría de estrés |
| evaluation_overload | enum | yes \| no | No | Sobrecarga reportada en semanas de evaluación |
| employability_concern | enum | low \| medium \| high | No | Nivel de preocupación por empleabilidad |
| support_network | enum | none \| limited \| adequate | No | Red de apoyo percibida |
| campus_activity_frequency | enum | low \| medium \| high | No | Frecuencia de participación en campus |
| previous_support_use | enum | never \| prior_18m \| earlier_than_18m | No | Historial de uso de apoyo previo a la encuesta |
| services_awareness | enum | aware \| unaware | No | Conocimiento de los servicios de apoyo |
| wellbeing_note | string | — | No | Aviso fijo: "synthetic category; not a diagnosis" |

---

## D2 — Eventos de servicios de apoyo (`D2_support_services.csv`)

**Llave:** `support_event_id` (PK). `student_id` y `service_id` son FK.

| Campo | Tipo | Valores / rango | Nullable | Descripción |
|---|---|---|---|---|
| support_event_id | string | — | No | Identificador único del evento de apoyo. **PK.** |
| student_id | string | — | No | Estudiante solicitante. **FK →** D1.student_id / D3.student_id |
| service_id | string | — | No | Servicio que atendió. **FK →** D6.service_id |
| request_date | date | — | No | Fecha de solicitud |
| appointment_date | date | — | No | Fecha de la cita agendada |
| wait_days | integer | 1–120 | No | Días de espera entre solicitud y cita |
| attended | boolean | true \| false | No | Si asistió a la cita |
| reason_code | enum | academic_pressure \| social_support \| career_concern \| sleep_and_routine \| preventive_guidance | No | Motivo codificado (no clínico) |
| contact_channel | enum | digital \| in_person \| phone | No | Canal de contacto |
| referral_outcome | enum | self_guided \| peer_support \| counseling \| career_service \| follow_up | No | Resultado de la orientación |

---

## D3 — Trayectoria académica (`D3_academic_trajectory.csv`)

Formato **largo**: varias filas por estudiante (una por período académico).

**Llave:** `student_period_id` (PK = `student_id` + `period_id`). `student_id` y `period_id` son FK.

| Campo | Tipo | Valores / rango | Nullable | Descripción |
|---|---|---|---|---|
| student_period_id | string | — | No | Llave única estudiante + período. **PK.** |
| student_id | string | — | No | Estudiante. **FK →** D1.student_id / D2.student_id |
| institution_id | enum | — | No | Institución |
| period_id | enum | — | No | Período académico. **FK →** D7.period_id |
| academic_stage | enum | early \| middle \| final | No | Etapa académica en ese período |
| credit_load | integer | 12–32 | No | Créditos matriculados |
| evaluation_count | integer | 2–10 | No | Número de evaluaciones mayores |
| average_grade | float | 1.0–7.0 | No | Promedio de notas (escala sintética) |
| grade_change | float | -3.0–3.0 | No | Cambio de nota vs. período anterior |
| attendance_rate | float | 0–1 | No | Proporción de asistencia |
| dropout_alert | enum | low \| medium \| high | No | Alerta sintética de riesgo de abandono |

---

## D4 — Testimonios (Oleada 2, no incluido aquí)

**Llave:** `testimony_id` (PK). No presente en `DataPack_Aethera_Oleada1`.

| Campo | Tipo | Valores / rango | Nullable | Descripción |
|---|---|---|---|---|
| testimony_id | string | — | No | Identificador único. **PK.** |
| source_type | enum | student_forum \| wellbeing_mailbox | No | Fuente ficticia de participación |
| country_context | enum | Chile \| Peru | No | Contexto país sintético |
| institution_id | enum | — | No | Institución |
| district_id | enum | — | No | Distrito |
| topic | enum | — | No | Tema principal no clínico |
| sentiment | enum | strained \| mixed \| hopeful | No | Tono sintético |
| text | string | — | No | Testimonio sintético en primera persona |

---

## D5 — Chats de orientación (Oleada 2, no incluido aquí)

**Llave:** `conversation_id` (PK). No presente en `DataPack_Aethera_Oleada1`.

| Campo | Tipo | Valores / rango | Nullable | Descripción |
|---|---|---|---|---|
| conversation_id | string | — | No | Identificador único de conversación. **PK.** |
| started_at | datetime | — | No | Timestamp sintético de inicio |
| country_context | enum | Chile \| Peru | No | Contexto país sintético |
| motive | enum | — | No | Motivo de orientación no clínico |
| referral | enum | — | No | Resultado ficticio de derivación |
| messages | array | — | No | Objetos ordenados de mensajes usuario/orientador |
| safety_note | string | — | No | Aviso de alcance |

---

## D6 — Mapa de servicios (`D6_services_map.geojson`)

GeoJSON `FeatureCollection`; cada `feature` = un servicio con `geometry` (punto) + `properties`.

**Llave:** `service_id` (PK, también es el `id` del feature).

| Campo (`properties`) | Tipo | Valores / rango | Nullable | Descripción |
|---|---|---|---|---|
| service_id | string | — | No | Identificador único del servicio. **PK.** FK usada por D2. |
| name | string | — | No | Nombre ficticio del servicio |
| service_type | enum | — | No | Categoría del servicio (ej. counseling, peer_support, career_guidance) |
| district_id | enum | — | No | Distrito donde está ubicado |
| schedule | string | — | No | Horario de atención |
| capacity | integer | 10–140 | No | Capacidad semanal de orientaciones |
| channels | array | — | No | Canales disponibles |
| eligibility | string | — | No | Nota de elegibilidad |
| referral_information | string | — | No | Información requerida para derivar |
| geometry | GeoJSON Point | — | No | Coordenadas en una grilla sintética (**no reales**) |

> Nota de verificación: los 15 puntos caen prácticamente sobre una sola línea recta (residuo máx. ~0.004 vs. rango 0.87) — es decir, no hay estructura espacial 2D real, solo 5 distritos × 3 tipos de servicio distribuidos linealmente.

---

## D7 — Calendario académico (`D7_calendar.csv` / `.ics`)

Mismo contenido en dos formatos: CSV (tabla) e ICS (estándar de calendario, importable en Google Calendar/Outlook).

**Llave:** `calendar_event_id` (PK). `period_id` es FK.

| Campo | Tipo | Valores / rango | Nullable | Descripción |
|---|---|---|---|---|
| calendar_event_id | string | — | No | Identificador único del evento. **PK.** |
| period_id | enum | — | No | Período académico. **FK →** D3.period_id |
| event_type | enum | period_start \| period_end \| evaluation_week \| university_activity \| wellbeing_activity | No | Categoría del evento |
| title | string | — | No | Título ficticio del evento |
| start_date | date | — | No | Fecha de inicio |
| end_date | date | — | No | Fecha de fin (inclusive) |
| institution_id | enum | — | No | Institución afectada, o "ALL" |
| district_id | enum | — | No | Distrito afectado, o "ALL" |
| evaluation_intensity | integer | 0–3 | No | Intensidad sintética de evaluaciones |

---

## Relaciones entre datasets

| Desde | Hacia | Cardinalidad |
|---|---|---|
| D1.student_id | D3.student_id | 0..1 a 4 |
| D2.student_id | D3.student_id | muchos a 4 |
| D2.service_id | D6.service_id | muchos a 1 |
| D3.period_id | D7.period_id | muchos a muchos eventos |

**Cadena de llaves, de un vistazo:**

```
D1 (student_id) ──┐
                  ├──> D3 (student_id + period_id) ──> D7 (period_id)
D2 (student_id) ──┘
D2 (service_id) ────> D6 (service_id)
```

---

## Métricas de misión (referencia)

Reconstrucción pública de los targets/métricas mencionados en el data pack (para orientar qué buscar, no resultados calculados):

| Métrica | Target | Numerador | Denominador | Filtros | Datasets | Nota |
|---|---|---|---|---|---|---|
| M1 | 0.41 | banda de ansiedad moderada/alta | respuestas válidas D1 | ninguno | D1 | Banda sintética; no es diagnóstico |
| M2 | 0.57 | evaluation_overload=yes | respuestas válidas D1 | asociación con caída de notas | D1+D3+D7 | r=0.48 es solo histórico |
| M3 | 0.63 | preocupación alta de empleabilidad | D1 etapa final | academic_stage=final | D1+D3 | — |
| M4 | 0.31 | support_network=none | respuestas válidas D1 | desagregación por migración | D1 | — |
| M5 | 0.68 | sintomático + nunca usó apoyo + sin evento en D2 | D1 sintomático | historial de vida desde D1 | D1+D2 | 18 meses de ausencia solo no es suficiente |
| M6 (conciencia) | 0.44 | services_awareness=unaware | respuestas válidas D1 | ninguno | D1+D6 | — |
| M6 (días de espera) | 42.0 | suma de wait_days | eventos D2 | esperas no nulas | D2 | target ±3 días |

---

*Documento de referencia generado a partir de `DATA_DICTIONARY.xlsm`. No contiene análisis, estadísticas calculadas sobre los datos reales, ni hallazgos — solo la estructura declarada del data pack.*
