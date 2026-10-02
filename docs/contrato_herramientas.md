# Contrato de herramientas AURA

El agente conversacional detecta el motivo, reúne preferencias y llama las funciones normales de Python. Todas las respuestas son serializables a JSON. Los motivos y su servicio ideal salen de `config/tablas.yaml`.

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

Recibe la misma estructura que `proponer_opciones` y agrega servicio ideal, franjas, distrito, grupo y fecha a `salidas/desencuentros_vivos.csv`. Devuelve `{"ok":true,"registro_id":"DES-0000002"}`. El archivo se escribe como UTF-8.

Los esquemas listos para tool calling se obtienen con `esquemas_herramientas()` en `aura.herramientas.esquemas`.
