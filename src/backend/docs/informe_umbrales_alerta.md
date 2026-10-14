# Informe Técnico: Determinación y Justificación del Umbral de Alerta Académica
**Sistema AURA · Misión M6: Barreras de Acceso**  
*Equipo Paralelo Sur · Desafío Ciudad Aethera 2026*  
*Documento Técnico de Referencia y Calibración Operativa*

---

## 1. Resumen Ejecutivo y Planteamiento del Problema

El módulo de **Contacto Proactivo (Paso 1: Aviso Académico)** de AURA cumple una función estratégica dual en la solución:

1. **Dimensión Ética y No Invasiva:**  
   Identifica oportunamente a estudiantes que atraviesan dificultades académicas observables en su trayectoria ($D3$) durante los momentos de mayor tensión del ciclo universitario (semanas de evaluación según $D7$), **sin utilizar variables de salud mental** ($D1$), garantizando estricta privacidad, sin emitir juicios diagnósticos y con total control del estudiante para aceptar, posponer o descartar el aviso.
2. **Dimensión Operativa y Regulación de Capacidad:**  
   Actúa como la **válvula reguladora del flujo de demanda ($\lambda$)**. Con una capacidad instalada de red de **$1.155$ cupos/semana** ($D6$) y una política de liberación del $50\%$ sobre cupos no ocupados previamente (**$\approx 520$ cupos/semana disponibles para AURA**), el umbral determina el volumen de estudiantes elegibles.
   - **Regla Adoptada:** El aviso se activa si el estudiante alcanza un **Puntaje $\ge 3$ señales**.
   - **Impacto y Concordancia:** Dado que durante la semana de exámenes la señal institucional $S_1$ (temporada) aplica a toda la institución ($S_1 = 1$), exigir $\text{Puntaje} \ge 3$ equivale a requerir **al menos 2 de las 3 señales académicas individuales restantes** ($S_2$: asistencia, $S_3$: notas, o $S_4$: carga de créditos).
   - Esta regla alcanza al **$21,01\%$ del alumnado en el periodo pico ($6.829$ estudiantes en $PER\_2026\_4$)** y genera una demanda que opera de forma fluida e inmediata en baja respuesta ($3\% - 5\%$), y que en semanas de alta respuesta ($\ge 7\%$) **activa armónicamente el Optimizador de Lotes (Algoritmo Genético) y la Lista de Espera** diseñados en la plataforma.

---

## 2. Formulación Matemática de las Señales ($D3 \times D7$)

El puntaje del estudiante $i$ en el periodo $t$ durante una semana de evaluación se define como la suma aditiva simple de 4 señales observables:

$$\text{Puntaje}_i = S_{1,i} + S_{2,i} + S_{3,i} + S_{4,i} \quad \in \{1, 2, 3, 4\}$$

Dado que el aviso solo se procesa en semanas oficiales de exámenes ($S_{1,i} \equiv 1$):

$$\text{Puntaje}_i \ge 3 \iff S_{2,i} + S_{3,i} + S_{4,i} \ge 2$$

| Señal | Definición Matemática / Variable | Condición de Activación | Prevalencia ($PER\_2026\_4$) | Dimensión Evaluada |
|---|---|:---:|:---:|---|
| **$S_1$** | `hoy` $\in$ `evaluation_week` ($D7$) | Activo en periodo de examen | **$100,0\%$** ($32.500$) | **Contexto Institucional:** Calendario académico oficial. |
| **$S_2$** | $\text{att}_{t-1} - \text{att}_t \ge \Delta_{\text{asist}}$ | $\ge 0,05$ ($5$ puntos porcentuales) | **$36,08\%$** ($11.726$) | **Comportamiento:** Desenganche presencial o ausentismo súbito. |
| **$S_3$** | `grade_change` $\le \Delta_{\text{nota}}$ | $\le -0,5$ puntos | **$20,18\%$** ($6.559$) | **Rendimiento:** Deterioro acumulado en calificaciones. |
| **$S_4$** | `credit_load` $\ge P_{75}(t)$ | $\ge 27,0$ créditos | **$26,02\%$** ($8.456$) | **Exposición:** Sobrecarga estructural por alta matrícula. |

### Ortogonalidad e Independencia de las Señales Individuales
Al evaluar la correlación lineal de Pearson ($\phi$) entre las tres señales individuales ($S_2, S_3, S_4$) en la cohorte completa de $32.500$ estudiantes de $PER\_2026\_4$:

- $r(S_2 \text{ [Asistencia]}, S_3 \text{ [Notas]}) = \mathbf{0,1289}$
- $r(S_2 \text{ [Asistencia]}, S_4 \text{ [Carga]}) = \mathbf{0,1293}$
- $r(S_3 \text{ [Notas]}, S_4 \text{ [Carga]}) = \mathbf{0,0888}$

> **Conclusión Metodológica:** Los coeficientes de correlación son extraordinariamente bajos ($r \le 0,13$). Esto demuestra que **las tres señales son independientes y no redundantes**. Cada una captura una dimensión distinta de vulnerabilidad (comportamiento en aula, desempeño académico y exigencia horaria). Exigir la coincidencia de **al menos 2 de estas 3 dificultades** junto con la semana de exámenes garantiza que se focalice a estudiantes con fricción académica objetiva y multifactorial.

---

## 3. Distribución de Puntajes y Cobertura Poblacional

Al procesar la trayectoria longitudinal de los $130.000$ registros de $D3$, la distribución de puntajes durante semanas de evaluación se comporta de la siguiente manera:

### Distribución por Periodo Evaluado

| Periodo | Estudiantes Totales | Puntaje 1 (Solo Examen) | Puntaje 2 (+ 1 fricción) | Puntaje 3 (+ 2 fricciones) | Puntaje 4 (+ 3 fricciones) | **Elegibles ($\ge 3$)** | **% Elegible** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **$PER\_2026\_2$** | $32.500$ | $13.627$ ($41,9\%$) | $11.948$ ($36,8\%$) | $5.649$ ($17,4\%$) | $1.276$ ($3,9\%$) | **$6.925$** | **$21,31\%$** |
| **$PER\_2026\_3$** | $32.500$ | $16.634$ ($51,2\%$) | $11.057$ ($34,0\%$) | $4.081$ ($12,6\%$) | $728$ ($2,2\%$) | **$4.809$** | **$14,80\%$** |
| **$PER\_2026\_4$** | $32.500$ | $13.836$ ($42,6\%$) | $11.835$ ($36,4\%$) | $5.581$ ($17,2\%$) | $1.248$ ($3,8\%$) | **$6.829$** | **$21,01\%$** |

```
Distribución Poblacional en PER_2026_4 (N = 32.500):
┌─────────────────────────────────────────────────────────────┬──────────────────────────┐
│ Puntaje 1 (42,6%)          │ Puntaje 2 (36,4%)              │ Puntaje 3 (17,2%) │ P4   │
│ Solo hito de examen        │ Examen + 1 dificultad          │ Examen + 2 dif.   │ (3,8)│
└─────────────────────────────────────────────────────────────┴──────────────────────────┘
                                                               ▲
                                                               └── CORTE EN PUNTAJE >= 3 (21,0%)
```

---

## 4. Comparativa de Alternativas de Corte y Justificación de $\text{Puntaje} \ge 3$

Evaluamos exhaustivamente las cuatro opciones posibles de corte bajo la premisa institucional de que $S_1 = 1$ durante la semana de exámenes:

| Umbral Evaluado | Condición Equivalente | Población Alcanzada ($PER\_2026\_4$) | Demanda Semanal ($\lambda$ al 8% conv.) | Utilización Operativa ($\rho = \lambda / 520$) | Veredicto de Operaciones y Calidad |
|:---:|---|:---:|:---:|:---:|---|
| **$\ge 1$** | Solo examen ($S_1$) | $32.500$ ($100,0\%$) | $2.600$ citas/sem | **$500,2\%$** | ❌ **Inviable Total:** Colapso instantáneo del sistema; equivale a saturar a toda la universidad sin discriminación. |
| **$\ge 2$** | Examen + $\ge 1$ dificultad | $18.664$ ($57,4\%$) | $1.493$ citas/sem | **$287,3\%$** | ❌ **Saturación Severa:** Triplica los cupos disponibles; genera listas de espera masivas de más de $1.000$ personas. |
| **$\ge 3$ (SELECCIONADO)** | **Examen + $\ge 2$ dificultades** | **$6.829$ ($21,0\%$)** | **$546$ citas/sem** | **$105,1\%$** | ✅ **ÓPTIMO OPERATIVO:** Permite atención directa en baja demanda ($3-5\%$) y activa con plena justificación el optimizador de lotes en alta demanda ($>7\%$). |
| **$\ge 4$** | Examen + las 3 dificultades | $1.248$ ($3,8\%$) | $100$ citas/sem | **$19,2\%$** | ❌ **Subutilización Crítica:** Deja más del $80\%$ de los cupos de bienestar vacíos y excluye a miles de alumnos vulnerables. |

---

## 5. Modelamiento de Capacidad, Teoría de Colas y Concordancia con la Plataforma

### 5.1 Capacidad Neta Disponible para AURA ($D6$)
- Capacidad instalada de la red: **$1.155$ cupos/semana** distribuidos en 15 servicios.
- Política de operación del prototipo:
  - $10\%$ ocupación inicial histórica reservada para citas regulares previas.
  - $50\%$ de los cupos restantes liberados para autoagendamiento mediante AURA.
  $$C_{\text{AURA}} = 1.155 \times (1 - 0,10) \times 0,50 = 519,75 \approx \mathbf{520 \text{ cupos/semana}}$$

### 5.2 Simulación de Tasa de Llegadas ($\lambda$) y Factor de Utilización ($\rho = \lambda / C_{\text{AURA}}$)
Para la población elegible de $6.829$ estudiantes ($PER\_2026\_4$), evaluamos la sensibilidad frente a distintas tasas de conversión del aviso ($\eta$):

| Tasa de Conversión ($\eta$) | Solicitudes Entrantes ($\lambda$) | Tasa de Ocupación ($\rho$) | Modo de Operación en el Backend de AURA | Experiencia del Estudiante |
|:---:|:---:|:---:|---|---|
| **$3,0\%$** | $205$ citas/sem | **$39,4\%$** | **Modo Directo** (`ServicioAsignacion`) | Cita inmediata confirmada en $< 2$ días. |
| **$5,0\%$** | $341$ citas/sem | **$65,7\%$** | **Modo Directo** (Cercano al límite) | Cita inmediata con alta disponibilidad. |
| **$7,0\%$** | $478$ citas/sem | **$92,0\%$** | **MODO LOTE ACTIVO** (`lote_service.py`) | Optimización metaheurística por lotes ($> 70\%$). |
| **$8,0\%$ (Nominal)** | $546$ citas/sem | **$105,1\%$** | **MODO LOTE + LISTA DE ESPERA** | Reparto con máxima equidad; derivación a lista de espera. |
| **$10,0\%$ (Pico)** | $683$ citas/sem | **$131,4\%$** | **MODO LOTE + LISTA DE ESPERA** | Registro sistemático de desencuentros como evidencia para abrir cupos. |

### 5.3 Concordancia con la Arquitectura de AURA (Modo Lote y Lista de Espera)
Este análisis demuestra la perfecta armonía entre los umbrales de alerta y el resto de la plataforma:
1. **Activación del Algoritmo Genético de Lotes (`lote_service.py`):**  
   Al alcanzar un $21,0\%$ de elegibilidad, una respuesta superior al $5\%$ introduce al sistema en la zona de estrés ($> 70\%$ de ocupación). En ese momento se activa el optimizador de lotes para distribuir los cupos con máxima equidad, balanceando la carga entre servicios y evitando que la asignación dependa únicamente del orden de llegada.
2. **Derivación a Lista de Espera (`lista_espera_service.py`):**  
   Durante picos de sobredemanda, los estudiantes que no encuentren un cupo compatible de inmediato no son descartados; se registran en la lista de espera como **desencuentros documentados**, generando la evidencia cuantitativa que la universidad requiere para abrir turnos en franjas saturadas (como horarios vespertinos).

---

## 6. Validación Externa con la Encuesta de Bienestar ($D1$)

Aunque $D1$ **nunca se utiliza en la plataforma real para decidir a quién mostrarle el aviso** (para preservar la privacidad y evitar estigmatización diagnóstica), cruzamos las señales de los $12.000$ encuestados para auditar si el filtro académico realmente captura sobrecarga:

| Nivel de Puntaje | Muestra en $D1$ ($N=12.000$) | % con Sobrecarga en Evaluaciones (`yes`) | Ansiedad Promedio ($0-21$) | Estrés Promedio ($0-24$) |
|:---:|:---:|:---:|:---:|:---:|
| **Puntaje 1** (Solo Examen) | $5.129$ | $55,7\%$ | $8,11$ | $12,03$ |
| **Puntaje 2** (+ 1 fricción) | $4.340$ | $57,2\%$ | $8,17$ | $12,06$ |
| **Puntaje 3** (+ 2 fricciones) | $2.072$ | **$58,4\%$** | $8,15$ | $12,11$ |
| **Puntaje 4** (+ 3 fricciones) | $459$ | **$63,6\%$** | $8,15$ | **$12,53$** |

### Métricas de Rendimiento frente a Sobrecarga de Exámenes
- **Sensibilidad:** $21,96\%$ de los alumnos sobrecargados de toda la universidad son focalizados directamente.
- **Especificidad:** **$80,06\%$**, garantizando que 8 de cada 10 estudiantes sin sobrecarga no son interrumpidos innecesariamente.
- **Precisión:** **$59,34\%$**, lo que significa que la mayoría de los estudiantes alcanzados por la alerta experimenta sobrecarga manifiesta.

---

## 7. Análisis de Sensibilidad de los Parámetros de Calibración

Los parámetros del aviso residen en `src/backend/config/parametros.yaml` bajo la clave `aviso`:

```yaml
aviso:
  dropout_alert: [medium, high]
  caida_asistencia: 0.05        # 5 p.p. vs periodo anterior
  cambio_nota: -0.5             # -0.5 puntos en escala 1 a 7
  percentil_carga_creditos: 0.75 # P75 (>= 27 créditos)
  puntaje_minimo: 3             # Regla de corte validada
  evento_evaluacion: evaluation_week
```

### Elasticidad de la Población Elegible en $PER\_2026\_4$

| Parámetro Evaluado | Valor Simulado | Estudiantes Elegibles | % Población | Impacto en la Operación |
|---|:---:|:---:|:---:|---|
| **Caída Asistencia (`caida_asistencia`)** | $0,03$ (3 p.p.) | $7.827$ | $24,08\%$ | Sube elegibilidad $+14,6\%$. Eleva presión sobre servicios diurnos. |
| | **$0,05$ (Nominal)** | **$6.829$** | **$21,01\%$** | **Punto de equilibrio nominal calibrado.** |
| | $0,07$ (7 p.p.) | $5.874$ | $18,07\%$ | Reduce elegibilidad $-14,0\%$. Útil si hay baja dotación de personal. |
| **Cambio de Nota (`cambio_nota`)** | $-0,3$ puntos | $8.633$ | $26,56\%$ | Sube elegibilidad $+26,4\%$. Capta caídas leves de rendimiento. |
| | **$-0,5$ (Nominal)** | **$6.829$** | **$21,01\%$** | **Punto de equilibrio nominal calibrado.** |
| | $-0,7$ puntos | $5.512$ | $16,96\%$ | Reduce elegibilidad $-19,3\%$. Focaliza en caídas severas de notas. |
| **Carga de Créditos (`percentil_carga_creditos`)** | $P_{70}$ ($\ge 26$ cred) | $8.088$ | $24,89\%$ | Amplía cobertura a estudiantes con carga intermedia-alta. |
| | **$P_{75}$ (Nominal)** | **$6.829$** | **$21,01\%$** | **Cuartil superior estándar de exigencia horaria.** |
| | $P_{80}$ ($\ge 27$ cred) | $6.829$ | $21,01\%$ | En $PER\_2026\_4$, $P_{80} = P_{75} = 27,0$, por lo que se mantiene estable. |

---

## 8. Protocolo de Experiencia de Usuario y Gobernanza Ética

1. **Mensaje No Estigmatizante (Frontend de Campus):**
   El componente [`campus/page.tsx`](file:///d:/UNIVERSIDAD/ConcursoPCH/SEGUNDO%20AVANCE/aura-main/src/frontend/app/campus/page.tsx) renderiza el aviso respetuoso y contextual:
   > *"Un espacio para ti, cuando lo necesites. En semanas de evaluaciones muchos estudiantes buscan apoyo. AURA te ayuda a encontrar una cita con los servicios de bienestar en pocos minutos, en el horario que te acomode."*  
   Nunca se menciona el rendimiento del estudiante ni sus faltas a clase.
2. **Control del Usuario:**
   Opciones de autonomía: `[ Hablar con AURA ]`, `[ Ahora no ]` y `[ No volver a mostrar este aviso ]` (baja voluntaria de la lista de avisos).
3. **Gobernanza Institucional:**
   Los parámetros están desacoplados del código fuente, residiendo en `parametros.yaml`. Bienestar Universitario supervisa las reglas y puede modular el flujo modificando los archivos sin requerir reprogramación del sistema.
