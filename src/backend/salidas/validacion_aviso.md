# Validación del aviso académico

**Regla:** en semana de evaluaciones (D7), el aviso aparece con al menos 2 de estas 3 señales: caída de asistencia (≥ 0,05 frente al período anterior), baja de nota (`grade_change` ≤ −0,5) y carga de créditos alta (percentil 0,75 del período). La semana de evaluaciones es la condición, no una señal; no se usa `dropout_alert`.

Fuente: D3 (señales), D7 (semanas de evaluación) y D1 (solo promedios por grupo). Generado por `experimentos/validar_aviso.py`.

## Cobertura y puntajes

Puntaje = cuántas de las 3 señales cumple cada estudiante.

| Periodo | Fecha evaluada | Estudiantes | Elegibles | % elegible | Puntaje 0 | Puntaje 1 | Puntaje 2 | Puntaje 3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PER_2026_2 | 2026-05-11 | 32500 | 6925 | 21.31% | 13627 | 11948 | 5649 | 1276 |
| PER_2026_3 | 2026-08-10 | 32500 | 4809 | 14.80% | 16634 | 11057 | 4081 | 728 |
| PER_2026_4 | 2026-11-09 | 32500 | 6829 | 21.01% | 13836 | 11835 | 5581 | 1248 |

## Validación agregada con D1

Se comparan promedios de anxiety_score solo para validar grupos; D1 no interviene en los filtros.

| Periodo | n elegibles | Ansiedad media elegibles | n no elegibles | Ansiedad media no elegibles |
|---|---:|---:|---:|---:|
| PER_2026_2 | 2568 | 8.12 | 9432 | 8.14 |
| PER_2026_3 | 1753 | 8.28 | 10247 | 8.11 |
| PER_2026_4 | 2531 | 8.15 | 9469 | 8.14 |

## Sensibilidad

Cambios de un umbral por vez para el periodo más reciente.

| Umbral | Valor | % elegible |
|---|---:|---:|
| caida_asistencia | 0.03 | 24.08% |
| caida_asistencia | 0.05 | 21.01% |
| caida_asistencia | 0.07 | 18.07% |
| cambio_nota | -0.3 | 26.56% |
| cambio_nota | -0.5 | 21.01% |
| cambio_nota | -0.7 | 16.96% |
| puntaje_minimo | 1 | 57.43% |
| puntaje_minimo | 2 | 21.01% |
| puntaje_minimo | 3 | 3.84% |
