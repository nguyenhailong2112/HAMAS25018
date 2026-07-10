# HAMAS25018

Vision Server for CCTV slot monitoring.

## Runtime

- Entry point: `app/main_vision_server.py`
- WebSocket: `/ws/slot-states`
- REST health: `/health`
- REST snapshot: `/api/v1/slots`
- Camera summary: `/api/v1/cameras`
- Monitor UI: `/monitor`

## Run

```bash
python app/main_vision_server.py
```
