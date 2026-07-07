# Communication API Update

Tai lieu nay chot contract giao tiep Vision sau khi thong nhat voi Tablet va FMS.

## 1. Public Rule

Vision chi lam nhiem vu:

- Check trang thai slot.
- Push state lien tuc.
- Mo API cho Tablet/FMS truy cap.

Vision khong xu ly business rule task.

For monitoring and integration debug, the Vision server also exposes:

- `GET /api/v1/events`
- `GET /api/v1/logs`
- `ws://VISION_SERVER_IP:8088/ws/events`

## 2. WebSocket

Endpoint:

```text
ws://VISION_SERVER_IP:8088/ws/slot-states
```

Payload push:

```json
{
  "timestamp": "2026-07-03T12:34:56.789012",
  "total_slots": 3,
  "slots": [
    {
      "camera_id": 1,
      "slot_id": 1,
      "state": "Car Full"
    },
    {
      "camera_id": 1,
      "slot_id": 2,
      "state": "Empty"
    },
    {
      "camera_id": 2,
      "slot_id": 1,
      "state": "Unknown"
    }
  ]
}
```

## 3. API Node State

API cu giu nguyen:

```text
GET /api/v1/node-state?nodeName=drop_kho_4
```

Response:

```json
{
  "timestamp": "2026-07-03T12:34:56.789012",
  "nodeName": "drop_kho_4",
  "state": "Car Full",
  "slot": {
    "camera_id": 1,
    "slot_id": 1,
    "nodeName": "drop_kho_4",
    "state": "Car Full"
  }
}
```

## 4. API Raw Node State

API moi cho process cu:

```text
GET /api/v1/node-state-raw?nodeName=drop_kho_4
```

Response:

```json
{
  "timestamp": "2026-07-03T12:34:56.789012",
  "nodeName": "drop_kho_4",
  "camera_id": "cam4",
  "slot_id": "A4",
  "state": "Car Full"
}
```

## 5. Events And Logs

Recent operational events:

```text
GET /api/v1/events?limit=50
```

Recent Vision logs:

```text
GET /api/v1/logs?limit=100
```

Realtime events stream:

```text
ws://VISION_SERVER_IP:8088/ws/events
```

Use cases:

- Camera connect/disconnect.
- Inference failure.
- Slot state change.
- Server start/stop.
- Integration troubleshooting.

## 6. Meaning Of State

- `Empty`: vi tri trong.
- `Car Full`: vi tri co hang.
- `Unknown`: chua chac chan hoac du lieu stale.

## 7. Rule For Integration

- Tablet co the dung `node-state` de hien thi theo node.
- FMS hoac he thong can format cu co the dung `node-state-raw`.
- WebSocket la kenh push realtime chinh.
- REST la kenh fallback va debug.
- `events` va `logs` la kenh xem tinh trang van hanh va callback-debug.
