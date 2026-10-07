# Reporte actualizado del motor AURA

Fecha base: 2026-10-01. Réplicas por escenario: 5; semillas: 42, 43, 44, 45, 46.
Lote base: 120 solicitudes; fracción nocturna 14.2%; ocupación histórica media 12.1%.

Las celdas de métricas muestran media ± desviación estándar muestral entre semillas.

## Asignación, espera y desencuentros

| Escenario | Método | % asignadas | Espera (días) | Diurnas | Nocturnas | Desencuentros |
|---|---|---:|---:|---:|---:|---:|
| x1 | Llegada | 100.0% ± 0.0 pp | 1.93 ± 0.09 | 1.95 ± 0.09 | 1.78 ± 0.49 | 0.00 ± 0.00 |
| x1 | Genético | 100.0% ± 0.0 pp | 1.91 ± 0.08 | 1.90 ± 0.07 | 1.90 ± 0.19 | 0.00 ± 0.00 |
| x2 | Llegada | 100.0% ± 0.0 pp | 3.26 ± 0.07 | 3.29 ± 0.09 | 3.13 ± 0.29 | 0.00 ± 0.00 |
| x2 | Genético | 100.0% ± 0.0 pp | 3.22 ± 0.07 | 3.22 ± 0.06 | 3.24 ± 0.09 | 0.00 ± 0.00 |
| x4.3 | Llegada | 99.9% ± 0.2 pp | 5.97 ± 0.05 | 6.06 ± 0.18 | 5.43 ± 0.66 | 0.60 ± 0.89 |
| x4.3 | Genético | 100.0% ± 0.1 pp | 5.93 ± 0.05 | 5.93 ± 0.05 | 5.93 ± 0.06 | 0.20 ± 0.45 |
| x6 | Llegada | 87.9% ± 0.7 pp | 6.93 ± 0.07 | 6.98 ± 0.04 | 6.66 ± 0.52 | 86.80 ± 4.97 |
| x6 | Genético | 87.7% ± 0.4 pp | 6.91 ± 0.07 | 6.91 ± 0.07 | 6.90 ± 0.09 | 88.80 ± 2.95 |
| x8 | Llegada | 69.8% ± 0.4 pp | 6.90 ± 0.08 | 6.85 ± 0.05 | 7.05 ± 0.38 | 289.80 ± 4.27 |
| x8 | Genético | 69.9% ± 0.5 pp | 6.91 ± 0.07 | 6.91 ± 0.07 | 6.91 ± 0.07 | 289.00 ± 4.58 |
| x4.3_lib25 | Llegada | 65.9% ± 0.5 pp | 6.94 ± 0.17 | 6.85 ± 0.10 | 7.29 ± 0.44 | 176.00 ± 2.55 |
| x4.3_lib25 | Genético | 65.9% ± 0.5 pp | 6.94 ± 0.17 | 6.94 ± 0.17 | 6.94 ± 0.19 | 176.00 ± 2.55 |

## Diferencia emparejada: Genético menos llegada

Cada fila compara ambos métodos con la misma semilla. Resumen descriptivo; no es una prueba de significancia.

| Escenario | Cambio asignados (pp) | Espera (d) | Diurnos (d) | Nocturnos (d) | Desencuentros |
|---|---:|---:|---:|---:|---:|
| x1 | +0.00 ± 0.00 | -0.02 ± 0.02 | -0.05 ± 0.07 | +0.12 ± 0.37 | +0.00 ± 0.00 |
| x2 | +0.00 ± 0.00 | -0.04 ± 0.01 | -0.07 ± 0.05 | +0.10 ± 0.25 | +0.00 ± 0.00 |
| x4.3 | +0.08 ± 0.11 | -0.03 ± 0.03 | -0.12 ± 0.17 | +0.51 ± 0.66 | -0.40 ± 0.55 |
| x6 | -0.28 ± 0.71 | -0.02 ± 0.05 | -0.07 ± 0.09 | +0.24 ± 0.45 | +2.00 ± 5.10 |
| x8 | +0.08 ± 0.19 | +0.01 ± 0.02 | +0.05 ± 0.07 | -0.15 ± 0.33 | -0.80 ± 1.79 |
| x4.3_lib25 | +0.00 ± 0.00 | -0.00 ± 0.00 | +0.09 ± 0.09 | -0.35 ± 0.27 | +0.00 ± 0.00 |

## Utilización media por servicio

La tabla se construye desde resultados en memoria: las columnas Llegada y Genético son porcentajes medios entre semillas.

| Escenario | Servicio | Llegada | Genético |
|---|---|---:|---:|
| x1 | SRV_AE_001 | 17.9% ± 7.1% | 17.9% ± 7.1% |
| x1 | SRV_AE_002 | 22.8% ± 1.8% | 18.4% ± 1.7% |
| x1 | SRV_AE_003 | 12.5% ± 1.9% | 12.5% ± 1.9% |
| x1 | SRV_AE_004 | 25.3% ± 3.5% | 25.3% ± 3.5% |
| x1 | SRV_AE_005 | 18.0% ± 3.6% | 13.7% ± 1.4% |
| x1 | SRV_AE_006 | 8.4% ± 0.7% | 7.9% ± 0.9% |
| x1 | SRV_AE_007 | 28.3% ± 4.3% | 27.1% ± 3.3% |
| x1 | SRV_AE_008 | 12.8% ± 2.3% | 13.3% ± 1.6% |
| x1 | SRV_AE_009 | 1.4% ± 1.0% | 1.6% ± 0.6% |
| x1 | SRV_AE_010 | 24.3% ± 5.2% | 22.7% ± 3.8% |
| x1 | SRV_AE_011 | 11.7% ± 3.1% | 12.6% ± 2.0% |
| x1 | SRV_AE_012 | 0.2% ± 0.5% | 0.4% ± 0.6% |
| x1 | SRV_AE_013 | 14.2% ± 4.2% | 17.8% ± 4.5% |
| x1 | SRV_AE_014 | 10.2% ± 0.9% | 12.9% ± 2.0% |
| x1 | SRV_AE_015 | 0.2% ± 0.4% | 0.2% ± 0.4% |
| x2 | SRV_AE_001 | 48.6% ± 3.2% | 45.0% ± 5.4% |
| x2 | SRV_AE_002 | 33.2% ± 2.3% | 32.0% ± 1.4% |
| x2 | SRV_AE_003 | 13.8% ± 1.7% | 13.8% ± 1.7% |
| x2 | SRV_AE_004 | 47.4% ± 3.7% | 42.1% ± 1.9% |
| x2 | SRV_AE_005 | 27.3% ± 5.2% | 27.3% ± 3.0% |
| x2 | SRV_AE_006 | 12.9% ± 0.6% | 12.9% ± 0.6% |
| x2 | SRV_AE_007 | 44.6% ± 3.8% | 42.5% ± 2.8% |
| x2 | SRV_AE_008 | 29.4% ± 1.8% | 30.3% ± 2.8% |
| x2 | SRV_AE_009 | 11.9% ± 1.0% | 11.6% ± 1.2% |
| x2 | SRV_AE_010 | 45.3% ± 1.4% | 45.0% ± 1.2% |
| x2 | SRV_AE_011 | 25.7% ± 2.0% | 27.9% ± 2.5% |
| x2 | SRV_AE_012 | 2.5% ± 1.4% | 2.5% ± 1.4% |
| x2 | SRV_AE_013 | 43.1% ± 2.6% | 42.8% ± 2.1% |
| x2 | SRV_AE_014 | 21.9% ± 2.6% | 24.6% ± 1.9% |
| x2 | SRV_AE_015 | 0.7% ± 0.8% | 0.9% ± 0.7% |
| x4.3 | SRV_AE_001 | 90.7% ± 3.2% | 90.7% ± 3.2% |
| x4.3 | SRV_AE_002 | 73.2% ± 1.8% | 73.2% ± 1.1% |
| x4.3 | SRV_AE_003 | 25.3% ± 4.3% | 25.0% ± 4.8% |
| x4.3 | SRV_AE_004 | 90.0% ± 6.8% | 88.9% ± 5.7% |
| x4.3 | SRV_AE_005 | 65.7% ± 4.0% | 65.0% ± 2.4% |
| x4.3 | SRV_AE_006 | 16.8% ± 2.2% | 17.1% ± 1.9% |
| x4.3 | SRV_AE_007 | 91.7% ± 6.1% | 89.6% ± 4.9% |
| x4.3 | SRV_AE_008 | 64.7% ± 1.9% | 66.1% ± 1.9% |
| x4.3 | SRV_AE_009 | 14.2% ± 2.5% | 14.2% ± 2.5% |
| x4.3 | SRV_AE_010 | 90.7% ± 5.3% | 86.7% ± 3.3% |
| x4.3 | SRV_AE_011 | 60.5% ± 5.3% | 63.3% ± 2.8% |
| x4.3 | SRV_AE_012 | 15.6% ± 1.3% | 15.6% ± 1.3% |
| x4.3 | SRV_AE_013 | 81.1% ± 4.0% | 79.7% ± 4.0% |
| x4.3 | SRV_AE_014 | 59.0% ± 4.1% | 61.3% ± 2.0% |
| x4.3 | SRV_AE_015 | 11.9% ± 0.8% | 11.9% ± 0.8% |
| x6 | SRV_AE_001 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x6 | SRV_AE_002 | 87.6% ± 3.8% | 86.0% ± 4.0% |
| x6 | SRV_AE_003 | 28.7% ± 2.4% | 28.7% ± 2.4% |
| x6 | SRV_AE_004 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x6 | SRV_AE_005 | 77.3% ± 3.2% | 77.0% ± 2.7% |
| x6 | SRV_AE_006 | 27.4% ± 1.1% | 27.4% ± 1.1% |
| x6 | SRV_AE_007 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x6 | SRV_AE_008 | 76.1% ± 1.8% | 76.9% ± 1.2% |
| x6 | SRV_AE_009 | 24.0% ± 2.7% | 23.7% ± 2.7% |
| x6 | SRV_AE_010 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x6 | SRV_AE_011 | 80.2% ± 2.2% | 79.8% ± 1.7% |
| x6 | SRV_AE_012 | 21.5% ± 1.2% | 21.7% ± 1.4% |
| x6 | SRV_AE_013 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x6 | SRV_AE_014 | 82.1% ± 3.0% | 80.8% ± 1.7% |
| x6 | SRV_AE_015 | 14.4% ± 1.5% | 14.4% ± 1.5% |
| x8 | SRV_AE_001 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x8 | SRV_AE_002 | 88.4% ± 3.0% | 88.4% ± 3.0% |
| x8 | SRV_AE_003 | 38.4% ± 2.8% | 38.4% ± 2.8% |
| x8 | SRV_AE_004 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x8 | SRV_AE_005 | 78.0% ± 2.5% | 78.0% ± 2.5% |
| x8 | SRV_AE_006 | 32.9% ± 5.4% | 33.4% ± 5.0% |
| x8 | SRV_AE_007 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x8 | SRV_AE_008 | 78.3% ± 2.9% | 78.6% ± 3.5% |
| x8 | SRV_AE_009 | 26.3% ± 2.5% | 26.3% ± 2.5% |
| x8 | SRV_AE_010 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x8 | SRV_AE_011 | 81.7% ± 2.6% | 82.4% ± 2.8% |
| x8 | SRV_AE_012 | 27.7% ± 3.8% | 27.5% ± 3.5% |
| x8 | SRV_AE_013 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x8 | SRV_AE_014 | 83.5% ± 3.6% | 83.5% ± 3.6% |
| x8 | SRV_AE_015 | 27.0% ± 3.6% | 26.9% ± 3.3% |
| x4.3_lib25 | SRV_AE_001 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x4.3_lib25 | SRV_AE_002 | 90.0% ± 7.0% | 90.0% ± 7.0% |
| x4.3_lib25 | SRV_AE_003 | 39.4% ± 7.5% | 39.4% ± 7.5% |
| x4.3_lib25 | SRV_AE_004 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x4.3_lib25 | SRV_AE_005 | 78.7% ± 3.8% | 78.7% ± 3.8% |
| x4.3_lib25 | SRV_AE_006 | 40.0% ± 2.2% | 40.0% ± 2.2% |
| x4.3_lib25 | SRV_AE_007 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x4.3_lib25 | SRV_AE_008 | 81.7% ± 3.2% | 81.7% ± 3.2% |
| x4.3_lib25 | SRV_AE_009 | 27.7% ± 4.4% | 27.7% ± 4.4% |
| x4.3_lib25 | SRV_AE_010 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x4.3_lib25 | SRV_AE_011 | 80.0% ± 2.1% | 80.0% ± 2.1% |
| x4.3_lib25 | SRV_AE_012 | 27.5% ± 5.4% | 27.9% ± 5.6% |
| x4.3_lib25 | SRV_AE_013 | 100.0% ± 0.0% | 100.0% ± 0.0% |
| x4.3_lib25 | SRV_AE_014 | 80.8% ± 6.3% | 80.8% ± 6.3% |
| x4.3_lib25 | SRV_AE_015 | 29.3% ± 2.4% | 28.9% ± 2.1% |

## Tiempo de ejecución

`Tiempo GA` es la corrida genética ponderada de cada semilla. La calibración de pagos se ejecutó una vez por escenario y se comparte entre sus cinco semillas.

| Escenario | Generaciones | Calibración compartida (s) | Tiempo total del escenario (s) | GA por semilla (s) |
|---|---:|---:|---:|---|
| x1 | 200 | 12.1 | 25.3 | 11.5, 11.6, 11.3, 10.7, 11.5 |
| x2 | 200 | 28.0 | 57.2 | 26.9, 25.8, 26.8, 26.2, 26.3 |
| x4.3 | 200 | 76.9 | 158.5 | 73.3, 77.1, 71.8, 73.3, 75.9 |
| x6 | 500 | 313.0 | 633.4 | 311.5, 314.0, 298.7, 293.9, 298.6 |
| x8 | 500 | 473.7 | 960.5 | 476.1, 475.8, 445.2, 477.7, 462.3 |
| x4.3_lib25 | 500 | 173.3 | 352.8 | 177.1, 163.6, 173.6, 162.7, 161.1 |

### Tiempo por réplica genética

| Escenario | Semilla | Generaciones | Tiempo GA (s) |
|---|---:|---:|---:|
| x1 | 42 | 200 | 11.5 |
| x1 | 43 | 200 | 11.6 |
| x1 | 44 | 200 | 11.3 |
| x1 | 45 | 200 | 10.7 |
| x1 | 46 | 200 | 11.5 |
| x2 | 42 | 200 | 26.9 |
| x2 | 43 | 200 | 25.8 |
| x2 | 44 | 200 | 26.8 |
| x2 | 45 | 200 | 26.2 |
| x2 | 46 | 200 | 26.3 |
| x4.3 | 42 | 200 | 73.3 |
| x4.3 | 43 | 200 | 77.1 |
| x4.3 | 44 | 200 | 71.8 |
| x4.3 | 45 | 200 | 73.3 |
| x4.3 | 46 | 200 | 75.9 |
| x6 | 42 | 500 | 311.5 |
| x6 | 43 | 500 | 314.0 |
| x6 | 44 | 500 | 298.7 |
| x6 | 45 | 500 | 293.9 |
| x6 | 46 | 500 | 298.6 |
| x8 | 42 | 500 | 476.1 |
| x8 | 43 | 500 | 475.8 |
| x8 | 44 | 500 | 445.2 |
| x8 | 45 | 500 | 477.7 |
| x8 | 46 | 500 | 462.3 |
| x4.3_lib25 | 42 | 500 | 177.1 |
| x4.3_lib25 | 43 | 500 | 163.6 |
| x4.3_lib25 | 44 | 500 | 173.6 |
| x4.3_lib25 | 45 | 500 | 162.7 |
| x4.3_lib25 | 46 | 500 | 161.1 |

## Escenarios y supuestos

- Demanda evaluada: x1, x2, x4.3, x6 y x8, más x4.3 con 25% de cupos libres liberados.
- Las corridas grandes (x6, x8 y x4.3 con liberación 0.25) usan 500 generaciones; x1, x2 y x4.3 estándar conservan 200.
- Las cinco optimizaciones monoobjetivo que forman la tabla de pagos se corren una vez por escenario; se comparte su normalización para comparar las semillas del mismo escenario.
- El lote base, supuestos de canal/distrito, motivos, agenda y cierres D7 siguen descritos en `README.md`.
- Las cinco semillas miden sensibilidad del lote, la ocupación inicial y el GA. La desviación es muestral (n−1).
- `comparacion.csv` contiene cada semilla; `resumen_5_semillas.csv` agrega medias y desviaciones; `utilizacion_detalle.csv` mantiene la utilización por semilla.
- La convergencia grafica el promedio del mejor Z por generación para cada escenario.

Para repetir la matriz: `python -m experimentos.experimento_genetico`. Se puede cambiar el conjunto de semillas con `--semillas 42 43 44 45 46`.

## Herramientas y filtros del aviso

La demo sin LLM se corre con `python -m experimentos.demo_herramientas`; las declaraciones JSON estan en `aura.herramientas.esquemas`.

Se configuro puntaje minimo 3: la cobertura es 12.91% en PER_2026_2, 8.12% en PER_2026_3 y 13.49% en PER_2026_4. Las medias agregadas de ansiedad elegibles/no elegibles son 9.05/8.00, 9.55/8.01 y 9.13/7.99. La diferencia se mantiene en los tres periodos; D1 no participa en elegibilidad.

Las senales individuales quedan solo en `aviso_auditoria.csv`. El Data Pack sigue externo y configurable en `config/parametros.yaml`.

## Validacion completa del aviso

Los avisos solo se consideran durante semanas de evaluación según D7.

## Cobertura y puntajes

| Periodo | Fecha evaluada | Estudiantes | Elegibles | % elegible | Puntaje 0 | Puntaje 1 | Puntaje 2 | Puntaje 3 | Puntaje 4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PER_2026_2 | 2026-05-11 | 32500 | 4195 | 12.91% | 11287 | 10191 | 6827 | 3349 | 846 |
| PER_2026_3 | 2026-08-10 | 32500 | 2640 | 8.12% | 14343 | 10171 | 5346 | 2187 | 453 |
| PER_2026_4 | 2026-11-09 | 32500 | 4383 | 13.49% | 11087 | 10081 | 6949 | 3518 | 865 |

## Validación agregada con D1

Se comparan promedios de anxiety_score solo para validar grupos; D1 no interviene en los filtros.

| Periodo | n elegibles | Ansiedad media elegibles | n no elegibles | Ansiedad media no elegibles |
|---|---:|---:|---:|---:|
| PER_2026_2 | 1561 | 9.05 | 10439 | 8.00 |
| PER_2026_3 | 979 | 9.55 | 11021 | 8.01 |
| PER_2026_4 | 1604 | 9.13 | 10396 | 7.99 |

## Sensibilidad

Cambios de un umbral por vez para el periodo más reciente.

| Umbral | Valor | % elegible |
|---|---:|---:|
| caida_asistencia | 0.03 | 15.12% |
| caida_asistencia | 0.05 | 13.49% |
| caida_asistencia | 0.07 | 11.89% |
| cambio_nota | -0.3 | 16.55% |
| cambio_nota | -0.5 | 13.49% |
| cambio_nota | -0.7 | 10.99% |
| puntaje_minimo | 1 | 65.89% |
| puntaje_minimo | 2 | 34.87% |
| puntaje_minimo | 3 | 13.49% |
