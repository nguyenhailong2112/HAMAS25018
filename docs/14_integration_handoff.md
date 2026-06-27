# Integration Handoff

## 1. Network

Vision Server binds to:

```text
0.0.0.0:8088
```

For site deployment, set the PC Vision Server IP in the `192.168.53.xxx` range.

Tablet/FMS/server tong can use:

```text
http://VISION_SERVER_IP:8088
ws://VISION_SERVER_IP:8088/ws/slot-states
```

## 2. Tablet Contract

Primary channel:

```text
WebSocket /ws/slot-states
```

Payload:

```json
{
  "timestamp": "2026-06-22T08:30:00.123+07:00",
  "total_slots": 22,
  "slots": [
    {
      "nodeName": "predock_oil_2",
      "state": "Empty"
    }
  ]
}
```

Allowed states:

- `Empty`
- `Occupied`
- `Unknown`

Tablet rule:

- `Unknown` must not be treated as `Empty`.
- Tablet owns mission validation and FMS task dispatch.
- Vision does not call FMS.

For task submission flow, Tablet should call `GET /api/v1/node-state?nodeName=...` for each selected node before enabling the final task submit button.

## 3. REST Endpoints

Health:

```text
GET /health
```

Server info and live contract:

```text
GET /api/v1/server-info
```

Single node lookup:

```text
GET /api/v1/node-state?nodeName=predock_oil_4
```

Slot snapshot:

```text
GET /api/v1/slots
```

Camera summary:

```text
GET /api/v1/cameras
```

Monitor UI:

```text
GET /monitor
```

## 4. IP Allowlist

Configure in `configs/runtime.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8088,
    "websocket_path": "/ws/slot-states",
    "rest_enabled": true,
    "ip_allowlist": [
      "192.168.53.10",
      "192.168.53.20"
    ]
  }
}
```

An empty list means allow all clients.

The allowlist accepts exact IP addresses and CIDR subnets:

```json
{
  "ip_allowlist": [
    "192.168.53.10",
    "192.168.53.20",
    "192.168.53.0/24"
  ]
}
```

## 5. Logs And Outputs

Runtime snapshot:

```text
outputs/runtime/slot_states_latest.json
```

State change history:

```text
outputs/history/slot_state_changes.jsonl
```

Application logs are written under the OS user config directory for `HAMAS25018`.
