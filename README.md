# HAMAS25018

Vision Server for CCTV slot occupancy monitoring.

## Runtime

- Entry point: `app/main_vision_server.py`
- WebSocket: `/ws/slot-states`
- REST health: `/health`
- REST snapshot: `/api/v1/slots`
- Camera summary: `/api/v1/cameras`
- Monitor UI: `/monitor`

## Responsibility

- Vision reads camera streams and detects slot state.
- Vision pushes `Empty / Occupied / Unknown` to Tablet / Caller App.
- Tablet validates business rules and sends tasks to FMS.
- Vision does not create tasks, dispatch AGV/FMR, or call FMS.

## Main Config

- `configs/cameras.json`
- `configs/ingest.json`
- `configs/rules.json`
- `configs/runtime.json`
- `configs/zones_cam1.json` to `configs/zones_cam6.json`

## Run

```bash
python app/main_vision_server.py
```

## Docs

- `docs/README.md`
- `docs/12_operation_runbook.md`
- `docs/13_current_state_report.md`
- `docs/14_integration_handoff.md`

