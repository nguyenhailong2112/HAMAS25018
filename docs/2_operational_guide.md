# 17. Vision Server Operational Guide

## What Vision provides

Vision is a read-only occupancy server. It:

- captures camera frames
- runs detection
- evaluates each configured slot ROI
- publishes slot state
- exposes REST, WebSocket, event, and log endpoints

Vision does not make warehouse business decisions.

## Network setup

- Server PC IP: configured by site
- Vision listens on the configured host/port in `configs/runtime.json`
- Client systems must be on the same allowlisted network or IP range

If a client gets `403`, its IP is not in the Vision allowlist.

## Primary integration flow

1. Camera pipeline updates slot states.
2. Vision stores the latest public snapshot.
3. Tablet or FMS calls `GET /api/v1/slots` or `GET /api/v1/slot-state`.
4. Tablet/FMS maps the returned `slot_id` to its own business node.
5. UI or downstream logic decides the actual action.

## How to test connectivity

### REST

```bash
curl http://192.168.53.111:8088/health
curl http://192.168.53.111:8088/api/v1/server-info
curl http://192.168.53.111:8088/api/v1/slots
curl "http://192.168.53.111:8088/api/v1/slot-state?slot_id=1"
```

### WebSocket

Connect to:

- `ws://192.168.53.111:8088/ws/slot-states`
- `ws://192.168.53.111:8088/ws/events`

Expected behavior:

- on connect, server sends the current snapshot or recent events immediately
- on update, server pushes new payloads automatically

## Success criteria

Connection is successful when:

- HTTP returns `200`
- WebSocket upgrades successfully
- payload contains `camera_id`, `slot_id`, `state`
- payload contains `camera_id`, `slot_id`, `state`
- monitor page loads and shows live tiles

## Failure cases

- `403`: client IP not allowlisted
- `404`: wrong path or slot not found
- `400`: missing `camera_id` or `slot_id`
- timeout / disconnect: network, browser, or server-side issue

## Monitoring

Use `/monitor` for live operator validation.

Use `/api/v1/events` and `/api/v1/logs` for troubleshooting.

## Performance notes

The current public contract is minimal and is already optimized for low-latency transmission:

- no business-name translation in the payload
- one compact snapshot stream
- per-slot lookup by key, not by business mapping

This is the right shape for site operation.
