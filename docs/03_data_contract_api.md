# Data Contract And API Spec

## 1. Contract Chính

Kênh tích hợp chính giữa Vision Server và Tablet là WebSocket.

Vision push trạng thái slot liên tục:

```text
ws://VISION_SERVER_IP:PORT/ws/slot-states
```

Payload phải nhỏ, ổn định, dễ parse.

## 2. Public State

Chỉ có 3 state public:

| State | Ý nghĩa | Tablet xử lý |
|---|---|---|
| `Empty` | Slot không có hàng | Có thể là điều kiện hợp lệ cho Store |
| `Occupied` | Slot có hàng | Cảnh báo nếu user muốn Store vào slot này |
| `Unknown` | Không xác định | Cảnh báo/fail-safe, không coi là Empty |

Không dùng thêm state khác trong payload chính nếu chưa thật sự cần.

## 3. WebSocket Snapshot Payload

Payload chuẩn:

```json
{
  "timestamp": "2026-06-22T08:30:00.123+07:00",
  "total_slots": 3,
  "slots": [
    {
      "camera_id": 1,
      "slot_id": 1,
      "state": "Occupied"
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

## 4. Field Rules

### `timestamp`

Thời điểm Vision tạo payload.

Format:

```text
ISO-8601 có timezone offset
```

Ví dụ:

```text
2026-06-22T08:30:00.123+07:00
```

### `total_slots`

Tổng số slot trong payload.

### `slots`

Danh sách state mới nhất của tất cả slot đang enabled.

### `camera_id`

ID camera.

Khuyến nghị dùng số nguyên nếu Tablet đã thống nhất như concept:

```json
"camera_id": 1
```

Nếu code nội bộ đang dùng `"cam1"`, runtime có thể map sang `1` ở contract layer.

### `slot_id`

ID slot trong camera hoặc ID slot theo layout đã thống nhất với Tablet.

Trong phase chính, `camera_id + slot_id` là khóa đủ rõ.

### `state`

Một trong:

- `Empty`
- `Occupied`
- `Unknown`

## 5. Optional Debug Fields

Không đưa vào payload chính mặc định. Chỉ bật khi Tablet/team debug yêu cầu.

Ví dụ:

```json
{
  "camera_id": 1,
  "slot_id": 2,
  "state": "Empty",
  "updated_at": "2026-06-22T08:30:00.123+07:00",
  "health": "online",
  "score": 0.86
}
```

Các field optional:

- `updated_at`
- `health`
- `score`
- `frame_id`
- `debug_reason`

Nguyên tắc: payload chính cho Tablet càng ít field càng tốt.

## 6. WebSocket Behavior

### 6.1 Push Mode

Vision có thể push theo một trong hai cách:

1. Push full snapshot định kỳ.
2. Push khi có thay đổi và heartbeat định kỳ.

Khuyến nghị giai đoạn đầu:

```text
Full snapshot định kỳ 2-5 Hz.
```

Lý do:

- Tablet dễ implement.
- Mất một message không làm sai state lâu.
- Không cần delta/reconcile logic phức tạp.

### 6.2 Heartbeat

Nếu chưa có state change, vẫn nên push snapshot hoặc heartbeat để Tablet biết Vision còn sống.

### 6.3 Reconnect

Tablet phải reconnect khi WebSocket mất kết nối. Vision không cần giữ session state riêng cho từng Tablet; mỗi Tablet reconnect xong nhận snapshot mới nhất.

## 7. REST API Tối Giản

REST không phải kênh chính. REST phục vụ:

- Debug.
- Health check.
- Future integration server tổng nếu cần.

### `GET /health`

Response:

```json
{
  "status": "online",
  "timestamp": "2026-06-22T08:30:00.123+07:00",
  "uptime_sec": 3600.5,
  "camera_count": 6,
  "online_camera_count": 6,
  "total_slots": 18,
  "unknown_slots": 0
}
```

### `GET /api/v1/slots`

Trả payload giống WebSocket snapshot.

### `GET /api/v1/cameras`

Response:

```json
{
  "timestamp": "2026-06-22T08:30:00.123+07:00",
  "cameras": [
    {
      "camera_id": 1,
      "name": "Camera 1",
      "health": "online",
      "slot_count": 3,
      "last_frame_at": "2026-06-22T08:29:59.900+07:00",
      "last_infer_at": "2026-06-22T08:30:00.020+07:00"
    }
  ]
}
```

## 8. JSON Snapshot File

Nên export file snapshot để debug:

```text
outputs/runtime/slot_states_latest.json
outputs/runtime/cameras/{camera_id}.json
outputs/history/slot_state_changes.jsonl
```

File `slot_states_latest.json` nên có cùng structure với WebSocket payload.

## 9. Backward/Future Compatibility

Các field như sau không nằm trong contract chính phase đầu:

- `storageBinCode`
- `ctnr_typ`
- `stg_bin_code`
- `indBind`
- `binding`
- HIK method mapping

Nếu sau này server tổng cần, có thể thêm endpoint riêng:

```text
GET /api/v1/integration/warehouse-slots
```

Không đưa các field này vào payload Tablet khi chưa cần, để giữ hệ thống gọn và dễ kiểm soát.

