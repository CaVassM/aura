# Informe de la regla del aviso académico

**AURA · Misión M6: Barreras de Acceso**  
**Equipo Paralelo Sur · Desafío Ciudad Aethera 2026**

## Regla implementada

El aviso se muestra únicamente durante una semana de evaluaciones de D7 y cuando la persona cumple al menos **2 de estas 3 señales** calculadas con D3:

1. Caída de asistencia de al menos 0,05 frente al período anterior.
2. Cambio de nota menor o igual que −0,5.
3. Carga de créditos en el percentil 0,75 o superior del período.

La semana de evaluaciones es la condición temporal; no suma puntos. `dropout_alert` no participa en el cálculo. D1 tampoco interviene en la selección individual.

## Resultados

| Período | Fecha de evaluación (D7) | Estudiantes | Elegibles | Porcentaje |
|---|---:|---:|---:|---:|
| PER_2026_2 | 2026-05-11 | 32.500 | 6.925 | 21,31 % |
| PER_2026_3 | 2026-08-10 | 32.500 | 4.809 | 14,80 % |
| PER_2026_4 | 2026-11-09 | 32.500 | 6.829 | 21,01 % |

Como validación agregada, se compararon promedios de `anxiety_score` de D1 entre personas elegibles y no elegibles, solo para los registros presentes en ambos conjuntos. Las medias fueron 8,12 vs. 8,14 en PER_2026_2; 8,28 vs. 8,11 en PER_2026_3; y 8,15 vs. 8,14 en PER_2026_4. No se almacenan ni se exponen valores individuales de ansiedad.

Los conteos y medias salen de [validacion_aviso.md](../salidas/validacion_aviso.md), generado por [validar_aviso.py](../experimentos/validar_aviso.py). Los umbrales activos están en [parametros.yaml](../config/parametros.yaml). La lógica del aviso del campus usa datos académicos simulados para los perfiles de demo; sus señales son las mismas, pero no son los datos individuales de D3.
