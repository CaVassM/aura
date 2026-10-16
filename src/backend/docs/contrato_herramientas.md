# Contrato de herramientas AURA

El agente conversacional detecta el motivo, reúne preferencias y llama las herramientas del motor a través de `aura.servicio.ServicioAsignacion` (`proponer_opciones`, `reservar`, `cancelar_cita`, `registrar_desencuentro`, o `ejecutar_herramienta(nombre, argumentos)` para despachar una llamada de tool calling tal como la emite el LLM). Todas las respuestas son serializables a JSON y el estado vive en RAM: se pierde al reiniciar el proceso. Los motivos y su servicio ideal salen de `config/tablas.yaml`.

## `proponer_opciones(solicitud, k=3)`

Devuelve **como máximo 3 opciones** (`max_opciones` en `parametros.yaml`; un `k` mayor se recorta). Primero van las del servicio que la persona pidió por nombre (`service_id_preferido` dentro de la solicitud: un id o un nombre como «Brújula») o, si no pidió ninguno, las del servicio ideal; las alternativas afines solo completan si faltan. Si se pasan `servicios_lote` (los de modo lote), cada uno sale como **una sola opción** de tipo `lote`.

Entrada:

```json
{
  "estudiante_id": "STU_DEMO_001",
  "motivo": "academic_pressure",
  "distrito": "DIST_GAIA",
  "franjas": [{"dia": "Tue", "desde": "09:00", "hasta": "18:00"}],
  "canales_aceptables": ["digital", "phone"],
  "grupo": "diurno"
}
```

Salida resumida:

```json
{
  "opciones": [{
    "opcion_id": "C0000123|digital",
    "tipo_opcion": "cupo",
    "service_id": "SRV_AE_001",
    "servicio_nombre": "Espacio Brújula Orientación",
    "tipo": "counseling",
    "distrito": "DIST_GAIA",
    "fecha": "2026-10-06",
    "hora_inicio": "09:00",
    "hora_fin": "10:00",
    "canal": "digital",
    "dias_espera": 5,
    "es_alternativa": false,
    "afinidad": 1.0
  }],
  "servicio_ideal": "counseling",
  "preferido": null,
  "mensaje": null
}
```

Una opción de lote no trae día ni hora: `{"opcion_id": "LOTE|SRV_AE_004", "tipo_opcion": "lote", "service_id", "servicio_nombre", "tipo", "distrito", "cupos_libres", "tiempo_respuesta_s", "mensaje": "Este servicio tiene mucha demanda; sus cupos se reparten en grupo. Te confirmo en unos segundos."}`.

Toda respuesta trae `mensaje`: el texto que redacta el backend para los casos especiales (sin cupos, servicio en lote, servicio pedido sin cupo), para que el LLM no tenga que inventar la explicación. Con `service_id_preferido`, `preferido` dice si se encontró el servicio y si tiene cupos; si no los tiene, trae su `fecha_mas_cercana` y la `mejor_alternativa_mismo_tipo` en otro servicio.

Si no existe opción: `{"opciones": [], "motivo_vacio": "sin_cupos_compatibles", "mensaje": "No encontré cupos…"}`. La propuesta no retiene ni reserva el cupo.

## `reservar(estudiante_id, opcion_id)`

Entrada: `{"estudiante_id":"STU_DEMO_001","opcion_id":"C0000123|digital"}`.

Salida: `{"ok":true,"cita":{"cita_id":"CITA-0000001", ...}}`. Si otra persona tomó el cupo: `{"ok":false,"error":"cupo_ya_tomado"}`.

## `cancelar_cita(cita_id)`

Entrada: `{"cita_id":"CITA-0000001"}`. Salida: `{"ok":true,"cita_id":"CITA-0000001"}`. Al cancelar, el cupo vuelve a estar disponible para una nueva reserva.

## `registrar_desencuentro(solicitud)`

Recibe la misma estructura que `proponer_opciones` y guarda en RAM servicio ideal, franjas, distrito, grupo y fecha. Devuelve `{"ok":true,"registro_id":"DES-0000002"}`. Los registros se consultan con `ServicioAsignacion.desencuentros()`.

## Qué acepta y qué devuelve ante entradas desordenadas

Un LLM rara vez manda el JSON perfecto. `aura.herramientas.validacion` normaliza lo razonable y, si algo no sirve, devuelve un error que dice cómo corregirlo (los valores válidos van en el `detalle`):

- `solicitud` puede llegar como objeto o como texto JSON; `k` como número o texto (se recorta a 3).
- `canales_aceptables`: lista o texto («videollamada, teléfono»); acepta `digital`/`phone`/`in_person` y sus nombres en español.
- `franjas`: lista (o una sola franja); días `Mon…Sun`, `Tuesday` o `martes`/`miércoles`; horas `9:00` o `09:00`; `desde` debe ser anterior a `hasta`.
- `distrito` (sin importar mayúsculas), `grupo` y `motivo` se validan contra el Data Pack y `tablas.yaml`.
- Una solicitud inválida en `proponer_opciones` devuelve `{"opciones": [], "motivo_vacio": "solicitud_invalida", "detalle": "…"}`; en `ejecutar_herramienta`, argumentos inservibles devuelven `{"ok": false, "error": "argumentos_invalidos", "detalle": "…"}`. Nada lanza excepciones.
- `proponer_opciones` sin resultados agrega un `mensaje` y una `sugerencia`: no ofrecer otros días, horas ni canales que la persona no dijo, registrar el desencuentro y ofrecer la lista de espera. Cada opción incluye `dia_semana` y `canal_label` en español.
- `reservar`: un `opcion_id` mal formado o con canal inexistente devuelve `opcion_invalida`; `cupo_ya_tomado` queda solo para cupos realmente ocupados.
- `cancelar_cita(cita_id, estudiante_id=None)`: con `estudiante_id` solo su dueño puede cancelar (otra persona recibe `cita_no_encontrada`).

El agente conversacional no llama a estas funciones tal cual: usa las suyas (`agente/herramientas.py`, [API del agente](api_agente.md)), que fijan el `estudiante_id` desde la sesión y pasan por la plataforma para que las citas queden registradas.

Los esquemas listos para tool calling se obtienen con `ServicioAsignacion.esquemas_herramientas()` (definidos en `aura.herramientas.esquemas`; incluyen `enum` de motivos, distritos, canales y días).
