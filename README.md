# HAMAS25018

Vision Server for CCTV slot monitoring.

## Runtime

- Entry point: `app/main_vision_server.py`
- WebSocket: `/ws/slot-states`
- REST health: `/health`
- REST snapshot: `/api/v1/slots`
- REST single slot: `/api/v1/slot-state?slot_id=1`
- Camera summary: `/api/v1/cameras`
- Monitor UI: `/monitor`

## Docs

- `docs/16_comn_api_update.md`
- `docs/17_operational_guide.md`

## Run

```bash
python app/main_vision_server.py
```
