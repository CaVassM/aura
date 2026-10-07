# Comparación de derivaciones D5 con AURA

Se analizaron 2500 conversaciones de D5; 0 tienen un motivo sin mapeo activo en `tablas.yaml`.
Cada conversación se evaluó de forma independiente sobre el mismo inventario nuevo; no se reservaron cupos.
La compatibilidad original usa el horario semanal de D6 y exige que quepa una sesión completa.
Las franjas usadas son day: lunes-viernes 09:00-18:00; evening con trabajo: 19:00-21:00; evening sin trabajo: 17:00-21:00.
‘Servicio que cierra a las 18:00’ indica que el horario D6 del servicio termina a esa hora.
La disponibilidad AURA se calcula con una agenda inicial nueva y sin reservas entre conversaciones.
AURA nunca devuelve una opción incompatible: o encuentra una cita que pasa sus filtros o registra un desencuentro.

## Resumen por modalidad y trabajo

| Grupo | n | D5 deriva a servicio que cierra 18:00 | D5 incompatible con horario | AURA opción compatible | AURA desencuentro |
|---|---:|---:|---:|---:|---:|
| day | 2093 | 66.41% | 0.00% | 100.00% | 0.00% |
| evening y trabaja | 55 | 78.18% | 78.18% | 76.36% | 23.64% |
| evening sin trabajo | 352 | 66.48% | 0.00% | 100.00% | 0.00% |

## Lectura y límites

El hallazgo principal es que D5 reparte las derivaciones de forma uniforme entre 15 servicios: cada uno recibe entre 166 y 167 conversaciones.
Al probar todos los mapeos de los 5 motivos a los 3 tipos de servicio, la coincidencia D5 queda entre 32.56% y 34.12%; con el mapeo provisional actual es 34.08%. Esto ronda un tercio, el nivel esperado por azar si hay tres tipos. Es evidencia descriptiva, no prueba de aleatoriedad ni de irrelevancia clínica.
AURA aplica la tabla configurada y selecciona el tipo ideal en 97.08% de las conversaciones. Este porcentaje solo mide consistencia interna con la tabla; no es una medida de acierto ni de pertinencia clínica.
La comparación mide si las derivaciones respetan las condiciones que declara el estudiante y las reglas actuales de AURA; no evalúa pertinencia clínica ni calidad de atención.

## Motivos en D5

| Motivo | Conversaciones |
|---|---:|
| academic_pressure | 509 |
| career_concern | 496 |
| service_navigation | 474 |
| sleep_and_routine | 515 |
| social_support | 506 |

## Archivos de salida

- `comparacion_d5.csv`: una fila por conversación con perfil extraído, resultado D5 y resultado AURA.
- `resumen_comparacion_d5.csv`: porcentajes agregados por modalidad, trabajo y denominadores.
- `comparacion_d5.png`: gráfico de barras agrupadas.
