# Resultados clave para el documento del concurso

Cada frase puede copiarse y adaptarse. Las cifras reportan medias y desviaciones entre semillas cuando se indica; las fuentes están al final de cada fila.

## Experimento de asignación

| Frase lista para usar | Fuente |
|---|---|
| “En el escenario base x1, ambos métodos asignaron el **100,00%** de las solicitudes; el Genético tuvo una espera media de **1,91 ± 0,08 días**.” | [resumen_5_semillas.csv](../salidas/resumen_5_semillas.csv) |
| “En x2, la cobertura se mantuvo en **100,00%**; la espera media del Genético fue **3,22 ± 0,07 días**.” | [resumen_5_semillas.csv](../salidas/resumen_5_semillas.csv) |
| “En x4.3, Llegada asignó **99,88%** y el Genético **99,96%**; sus esperas medias fueron **5,97** y **5,93 días**, respectivamente.” | [resumen_5_semillas.csv](../salidas/resumen_5_semillas.csv) |
| “En x6, la cobertura fue **87,94%** para Llegada y **87,67%** para el Genético; aún hubo en promedio **88,80** solicitudes sin cita con el Genético.” | [resumen_5_semillas.csv](../salidas/resumen_5_semillas.csv) |
| “En x8, ambos métodos asignaron cerca de **70%**; el Genético alcanzó **69,90%** y dejó **289,00 ± 4,58** solicitudes sin cita.” | [resumen_5_semillas.csv](../salidas/resumen_5_semillas.csv) |
| “Con x4.3 y **25%** de liberación, ambos asignaron **65,89%**; se mantuvieron **176,00 ± 2,55** desencuentros.” | [resumen_5_semillas.csv](../salidas/resumen_5_semillas.csv), [parametros.yaml](../config/parametros.yaml) |
| “El costo computacional creció con la demanda: el escenario x8 tomó **960,5 segundos** en total y x1 tomó **25,3 segundos**, incluyendo calibración y las cinco semillas.” | [metadatos.json](../salidas/metadatos.json) |
| “En las corridas de **500 generaciones**, cada repetición genética tardó aproximadamente **294–314 segundos** en x6 y **445–478 segundos** en x8.” | [reporte.md](../salidas/reporte.md) |
| “En x6, la espera media genética fue **6,91 días** para estudiantes diurnos y **6,90 días** para nocturnos; en x8, fue **6,91 días** para ambos grupos, dentro del redondeo reportado.” | [resumen_5_semillas.csv](../salidas/resumen_5_semillas.csv) |
| “El Genético no aumenta la cantidad de cupos: bajo escasez, la cobertura siguió limitada por oferta; su resultado más claro fue equilibrar las esperas diurnas y nocturnas.” | [reporte.md](../salidas/reporte.md), [resumen_5_semillas.csv](../salidas/resumen_5_semillas.csv) |

Los escenarios corrieron con población **50**, semillas **42–46**, generaciones **200** en x1/x2/x4.3 y **500** en x6/x8/x4.3 con liberación reducida. Fuente: [parametros.yaml](../config/parametros.yaml). Los tiempos por escenario y por semilla están en [reporte.md](../salidas/reporte.md).

## Avisos

| Frase lista para usar | Fuente |
|---|---|
| “Con puntaje mínimo **3**, resultó elegible **12,91%** del período PER_2026_2, **8,12%** de PER_2026_3 y **13,49%** de PER_2026_4.” | [validacion_aviso.md](../salidas/validacion_aviso.md), [parametros.yaml](../config/parametros.yaml) |
| “La ansiedad media agregada de D1 fue mayor en elegibles que en no elegibles en los tres períodos: **9,05 vs 8,00**, **9,55 vs 8,01** y **9,13 vs 7,99**.” | [validacion_aviso_d1_agregada.csv](../salidas/validacion_aviso_d1_agregada.csv) |
| “D1 se usó solo para comparar promedios por grupo; no participa en la selección individual ni revela ansiedad por estudiante.” | [filtros.py](../aura/aviso/filtros.py), [validacion_aviso_d1_agregada.csv](../salidas/validacion_aviso_d1_agregada.csv) |

## Derivaciones D5 frente a AURA

| Frase lista para usar | Fuente |
|---|---|
| “D5 repartió **2.500** derivaciones de forma uniforme entre **15** servicios: cada servicio recibió **166 o 167** conversaciones.” | [reporte_comparacion_d5.md](../salidas/reporte_comparacion_d5.md), [comparacion_d5.csv](../salidas/comparacion_d5.csv) |
| “Al probar mapeos razonables entre los motivos y los **3** tipos de servicio, la coincidencia D5 se mantuvo cerca de **1/3**, el nivel esperado por azar con tres tipos.” | [reporte_comparacion_d5.md](../salidas/reporte_comparacion_d5.md) |
| “AURA selecciona opciones según su tabla provisional; el porcentaje que coincide con el tipo ideal mide consistencia con esa regla, no acierto ni pertinencia clínica.” | [reporte_comparacion_d5.md](../salidas/reporte_comparacion_d5.md), [tablas.yaml](../config/tablas.yaml) |
| “AURA solo propone opciones que pasan sus filtros: encuentra una opción compatible con horario, canal, afinidad y disponibilidad, o registra un desencuentro.” | [comparacion_d5.csv](../salidas/comparacion_d5.csv), [reglas.py](../aura/motor/reglas.py), [reporte_comparacion_d5.md](../salidas/reporte_comparacion_d5.md) |
| “En el subgrupo evening que trabaja (**n=55**), **78,18%** de las derivaciones D5 va a servicios que cierran a las 18:00 y **78,18%** no cabe en el horario declarado; AURA ofrece una opción compatible en **76,36%** y registra desencuentro en **23,64%**.” | [resumen_comparacion_d5.csv](../salidas/resumen_comparacion_d5.csv), [reporte_comparacion_d5.md](../salidas/reporte_comparacion_d5.md) |
| “En evening sin trabajo (**n=352**), **66,48%** de las derivaciones D5 va a servicios que cierran a las 18:00, pero todas caben en la franja 17:00–21:00; AURA encuentra opción compatible en **100%**.” | [resumen_comparacion_d5.csv](../salidas/resumen_comparacion_d5.csv), [reporte_comparacion_d5.md](../salidas/reporte_comparacion_d5.md) |
| “En day (**n=2.093**), **66,41%** de las derivaciones D5 va a servicios que cierran a las 18:00 y todas caben en 09:00–18:00; AURA encuentra opción compatible en **100%**.” | [resumen_comparacion_d5.csv](../salidas/resumen_comparacion_d5.csv), [reporte_comparacion_d5.md](../salidas/reporte_comparacion_d5.md) |

La comparación mide compatibilidad con lo que declara la persona; no juzga corrección clínica. La clasificación por horario separa day, evening con trabajo y evening sin trabajo.

## Capacidad ociosa y tiempo de espera

| Frase lista para usar | Supuestos y fuente |
|---|---|
| “Con la capacidad que hoy está ociosa y liberando el **50%** de los cupos disponibles, la espera simulada baja de una media observada de **41,96 días** en D2 (≈**42**) a **1,91 días** en el escenario de demanda actual (x1).” | La ocupación por servicio se estima con eventos/capacidad semanal de D2; luego se libera el 50% de los cupos restantes. x1 usa demanda base, horizonte de 2 semanas y sesiones de 60 minutos. Fuentes: D2 `D2_support_services.csv`, columna `wait_days` (9.400 eventos; Data Pack de origen); [resumen_5_semillas.csv](../salidas/resumen_5_semillas.csv), [parametros.yaml](../config/parametros.yaml), [experimento_genetico.py](../experimentos/experimento_genetico.py). |

## Conocimiento de los servicios y sesgo declarado

| Frase lista para usar | Fuente |
|---|---|
| “El sesgo intencional declarado hacia estudiantes evening considera que **54,7% (769/1.405)** desconoce los servicios, frente a **42,6% (4.511/10.595)** de estudiantes day.” | D1 `study_mode` × `services_awareness`, calculado desde `D1_wellbeing_survey.csv` (12.000 respuestas; Data Pack de origen). |

## Predictor y costo

| Frase lista para usar | Fuente |
|---|---|
| “La regresión logística sin D1 obtuvo AUC **0,5407**, gradient boosting **0,5092** y el baseline suavizado **0,4998**, valores cercanos al azar para la predicción individual.” | [metricas_modelos.csv](../salidas/metricas_modelos.csv) |
| “El costo aplica una probabilidad de asistencia por canal, compartida entre personas: **0,725** digital, **0,707** phone y **0,667** presencial.” | [parametros.yaml](../config/parametros.yaml), implementación en [costo.py](../aura/motor/costo.py) |

La fila exploratoria “Logística + D1” del archivo de métricas tiene AUC **0,5501**; se identifica expresamente como exploratoria y no se emplea en los filtros. Fuente: [metricas_modelos.csv](../salidas/metricas_modelos.csv).
