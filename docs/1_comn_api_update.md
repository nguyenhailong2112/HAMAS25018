# 16. Vision Public Communication Update

## Scope

Vision Server only publishes what Vision can verify locally:

- `camera_id`
- `slot_id`
- `state`
- `timestamp`
- `total_slots`

## Public state labels

- `Empty`
- `Car Full`
- `Unknown`

`Unknown` must not be treated as `Empty`.

## Public payload format

### Full snapshot

```json
{
  "timestamp": "2026-07-13T08:15:30.123+07:00",
  "total_slots": 17,
  "slots": [
    {
      "camera_id": "cam1",
      "slot_id": "A1",
      "state": "Car Full"
    },
    {
      "camera_id": "cam1",
      "slot_id": "A2",
      "state": "Empty"
    }
  ]
}
```

### Single slot

```json
{
  "timestamp": "2026-07-13T08:15:30.123+07:00",
  "camera_id": "cam1",
  "slot_id": "A1",
  "state": "Car Full"
}
```

## REST API

### 1. Get all slot states

- `GET /api/v1/slots`

Returns the full snapshot payload.

Example:

```bash
curl http://192.168.53.111:8088/api/v1/slots
```

### 2. Get one slot state

- `GET /api/v1/slot-state?slot_id=1`

Returns the state of one slot only.

Example:

```bash
curl "http://192.168.53.111:8088/api/v1/slot-state?slot_id=1"
```

### 3. Server info

- `GET /api/v1/server-info`

Returns service metadata, listen address, supported endpoints, and public slot contract.

### 4. Health

- `GET /health`

Returns runtime health and uptime.

### 5. Logs

- `GET /api/v1/logs?limit=100`

Returns recent runtime log lines.

### 6. Events

- `GET /api/v1/events?limit=50`

Returns recent Vision events such as startup, runtime changes, inference failures, and slot changes.

### 7. Camera summary

- `GET /api/v1/cameras`

Returns camera health and last inference metadata.

## WebSocket

### 1. Slot snapshot stream

- `ws://192.168.53.111:8088/ws/slot-states`

The server pushes the same public snapshot format as `/api/v1/slots`.

### 2. Event stream

- `ws://192.168.53.111:8088/ws/events`

The server pushes event objects for runtime monitoring.

## Monitor UI

- `/monitor`

Use this for quick visual validation of all camera/slot outputs. The monitor displays:

- total slots
- empty count
- car full count
- unknown count
- per-camera slot tiles

## Integration rule

Downstream systems must match `slot_id` on their side if they need business names or warehouse mapping.

Vision exposes only `camera_id`, `slot_id`, and `state` in public payloads.
