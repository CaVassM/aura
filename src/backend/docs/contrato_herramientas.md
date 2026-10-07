# Contrato de herramientas AURA

El agente conversacional detecta el motivo, reúne preferencias y llama las herramientas del motor a través de `aura.servicio.ServicioAsignacion` (`proponer_opciones`, `reservar`, `cancelar_cita`, `registrar_desencuentro`, o `ejecutar_herramienta(nombre, argumentos)` para despachar una llamada de tool calling tal como la emite el LLM). Todas las respuestas son serializables a JSON y el estado vive en RAM: se pierde al reiniciar el proceso. Los motivos y su servicio ideal salen de `config/tablas.yaml`.

## `proponer_opciones(solicitud, k=3)`

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
  "servicio_ideal": "counseling"
}
```

Si no existe opción: `{"opciones": [], "motivo_vacio": "sin_cupos_compatibles"}`. La propuesta no retiene ni reserva el cupo.

## `reservar(estudiante_id, opcion_id)`

Entrada: `{"estudiante_id":"STU_DEMO_001","opcion_id":"C0000123|digital"}`.

Salida: `{"ok":true,"cita":{"cita_id":"CITA-0000001", ...}}`. Si otra persona tomó el cupo: `{"ok":false,"error":"cupo_ya_tomado"}`.

## `cancelar_cita(cita_id)`

Entrada: `{"cita_id":"CITA-0000001"}`. Salida: `{"ok":true,"cita_id":"CITA-0000001"}`. Al cancelar, el cupo vuelve a estar disponible para una nueva reserva.

## `registrar_desencuentro(solicitud)`

Recibe la misma estructura que `proponer_opciones` y guarda en RAM servicio ideal, franjas, distrito, grupo y fecha. Devuelve `{"ok":true,"registro_id":"DES-0000002"}`. Los registros se consultan con `ServicioAsignacion.desencuentros()`.

Los esquemas listos para tool calling se obtienen con `ServicioAsignacion.esquemas_herramientas()` (definidos en `aura.herramientas.esquemas`).
