# Decisiones del equipo (resueltas y pendientes)

Los parámetros listados como **PROVISIONAL** son valores activos del prototipo, no recomendaciones definitivas. Los renglones comentados en YAML son candidatos de conversación: no están habilitados y no cambian el motor ni las herramientas.



## Resueltas para el Entregable 2

| Decisión | Decisión aplicada | Fuente |
|---|---|---|
| Umbral de modo lote | **75 %**, un único valor en YAML; también fija el nivel «alta» de ocupación. | [parametros.yaml](../config/parametros.yaml) |
| Aviso académico | En semana de evaluaciones (D7), al menos **2 de 3** señales: asistencia, nota y carga de créditos. La semana es condición, no señal; no se usa `dropout_alert`. | [como_funciona.md](como_funciona.md), [validacion_aviso.md](../salidas/validacion_aviso.md) |
| R7 | Una cita activa por persona y tipo de servicio. | [parametros.yaml](../config/parametros.yaml) |
| Propuestas y servicio preferido | Máximo 3 opciones; el servicio pedido por nombre va primero y un servicio saturado se ofrece como opción de tipo `lote`. | [api_agente.md](api_agente.md) |
| Desencuentros | Entrar a un lote no es desencuentro; se registra solo cuando no existe una opción compatible. Se evita duplicar el mismo servicio ideal y franja dentro de una conversación. | [api_agente.md](api_agente.md), [contrato_herramientas.md](contrato_herramientas.md) |
| Guardrails y errores de herramientas | Respuesta fija ante crisis, solicitudes clínicas o datos de profesionales; ante llamada mal formada se reintenta una vez y luego se usa una respuesta segura. | [guardrails.py](../agente/guardrails.py), [api_agente.md](api_agente.md) |
| Modelo | Qwen 3.5 4B (`qwen3.5:4b`), pesos abiertos, local en Ollama. | [config.py](../agente/config.py) |
| Datos | El Data Pack no se redistribuye; D1 solo participa en la validación agregada. | [README raíz](../../../README.md) |
| Escenario de demo | Demanda ×6, 10 % de vespertinos que trabajan, `hoy = 2026-11-15`; espera = fecha de cita menos fecha de solicitud, como D2. | [como_funciona.md](como_funciona.md) |

## Pendientes

| Decisión | Valor actual | Alternativas para discutir | Qué cambiaría en los resultados | Fuente |
|---|---|---|---|---|
| Afinidad y umbral | Matriz 1,0 / 0,6 / 0,3; 0,6 / 1,0 / 0,4; 0,3 / 0,4 / 1,0. Corte **0,50**. | Revisar cada par con responsables de servicios; subir o bajar el corte después de validar pertinencia. | Cambia qué servicios alternativos pasan R2, el número de opciones, la espera y los desencuentros. | [tablas.yaml](../config/tablas.yaml), [parametros.yaml](../config/parametros.yaml) |
| `academic_pressure` | counseling | Confirmar con orientación o elegir otro tipo existente. | Cambiaría el servicio ideal y la tasa de motivo coherente en D5. | [tablas.yaml](../config/tablas.yaml) |
| `sleep_and_routine` | counseling | Confirmar o revisar con orientación. | Cambiaría candidatos y alternativas disponibles para esas solicitudes. | [tablas.yaml](../config/tablas.yaml) |
| `social_support` | peer_support | Confirmar o revisar con orientación. | Cambiaría el tipo ideal y la elegibilidad de alternativas por afinidad. | [tablas.yaml](../config/tablas.yaml) |
| `career_concern` | career_guidance | Confirmar o revisar con orientación. | Cambiaría qué cita cuenta como ideal frente a alternativa. | [tablas.yaml](../config/tablas.yaml) |
| `preventive_guidance` | counseling | Confirmar; considerar derivación a orientación general o pares. | Cambiaría el servicio esperado para solicitudes preventivas; no aparece como motivo en D5 actual. | [tablas.yaml](../config/tablas.yaml), [baselines.py](../aura/motor/baselines.py) |
| `service_navigation` | **peer_support**, marcado PROVISIONAL; aparece en **474** conversaciones D5. | Confirmar peer_support, elegir counseling o crear una ruta humana de orientación. | Cambiarlo altera qué tipo cuenta como ideal y qué alternativas pasan por afinidad; la tabla no es una validación clínica. | [reporte_comparacion_d5.md](../salidas/reporte_comparacion_d5.md), [tablas.yaml](../config/tablas.yaml) |
| `work_study_balance` | Sin mapeo activo; D4 contiene **296** testimonios con ese tema. | counseling, career_guidance o revisar horarios/canales antes de mapear servicio. | Cambiaría la derivación para solicitudes que mencionan simultáneamente estudio y trabajo; no está en D5 como motivo actual. | [D4_testimonials.json](../../D4_testimonials.json), [tablas.yaml](../config/tablas.yaml) |
| Fracción liberada | **0,50** de los cupos disponibles tras ocupación inicial. | Mantener el caso estándar o usar **0,25**, ya probado como escenario de escasez. | Menos cupos liberados reduce asignaciones y aumenta desencuentros; también redistribuye utilización. | [parametros.yaml](../config/parametros.yaml), [resumen_5_semillas.csv](../salidas/resumen_5_semillas.csv) |
| Duración de sesión | **60 minutos**. | Revisar con operaciones y servicios usando su duración real. | Cambia cuántos bloques caben en horarios D6 y, por tanto, la oferta calculada. | [parametros.yaml](../config/parametros.yaml), [agenda.py](../aura/motor/agenda.py) |
| Pesos de Z | Z1 **0,35**; Z2 **0,25**; Z3 **0,10**; Z4 **0,20**; Z5 **0,10**. | Dar más importancia a cobertura, espera, balance de servicio, equidad de grupos o afinidad según prioridad institucional; mantener suma normalizada. | Cambia el intercambio que el Genético acepta entre cobertura, espera, utilización, equidad y ajuste del servicio. | [parametros.yaml](../config/parametros.yaml), [reporte.md](../salidas/reporte.md) |
| Beta del costo | **5,0**. | Revisar cuánto debe pesar afinidad frente a espera ajustada por canal. | Un beta mayor penaliza más las alternativas con menor afinidad; uno menor puede preferir citas más tempranas. | [parametros.yaml](../config/parametros.yaml), [costo.py](../aura/motor/costo.py) |
| Modo lote | **Resuelto:** umbral 75 %, la persona elige la opción de tipo `lote` y entrar no registra desencuentro. **Pendiente:** confirmar ventana de 30 s y tope de 5, y si los lotes deben admitir solicitudes que también tienen opciones directas. | Revisar si el cierre debe ser más corto en la demo de video. | Cambia cuánto espera una persona y cuántas solicitudes compiten juntas. | [parametros.yaml](../config/parametros.yaml), [como_funciona.md](como_funciona.md) |
| Protocolo de crisis del agente | **Implementado:** responde con texto fijo, remite a emergencias y no agenda en ese mensaje. **Pendiente:** Bienestar debe confirmar el texto institucional, la línea de ayuda de la red (`AURA_LINEA_AYUDA`) y si se avisa a un profesional humano. | Definir el texto y los datos de contacto institucionales. | Cambia la respuesta ante mensajes sensibles; no afecta la asignación. | [crisis.py](../agente/crisis.py) |
| Vida académica simulada del campus | Cursos, horarios, notas y asistencia **inventados** para los 4 perfiles de la demo; escala 1,0–7,0 (aprueba 4,0), asistencia mínima 70 %, sin clases en semanas de evaluación. Lo real es el calendario D7. El agente solo accede a la **asistencia**. | Cuando existan D3 y la matrícula real: leer de ahí; confirmar mínimo de asistencia, escala y si hay clases en semanas de evaluación y en la pausa de bienestar de Gaia. | Solo cambia lo que muestran Mis cursos, Calificaciones y Calendario y lo que el agente cuenta de la asistencia; no afecta el motor ni el aviso. | [academico_repository.py](../app/repositories/academico_repository.py), [api_agente.md](api_agente.md) |
| Lista de espera y aviso proactivo | Lista de espera: se avisa dentro del campus, en orden de llegada, sin retener cupo. Aviso proactivo **resuelto:** 2 de 3 señales en semana de evaluación, con opción de baja. | Retención temporal de cupo, caducidad y canales externos; revisar si D7 debe diferenciar evaluaciones intermedias y finales. | Cambia la recuperación de desencuentros y el momento de contacto. | [lista_espera_service.py](../app/services/lista_espera_service.py), [aviso_proactivo_service.py](../app/services/aviso_proactivo_service.py) |

## Propuesta de trabajo

Siguen pendientes la validación de los mapas de motivo y afinidad con orientación y la revisión de los pesos de equidad frente a cobertura entre semillas. Los parámetros marcados **PROVISIONAL** siguen siendo supuestos del prototipo.
