# Configuration Spec

## 1. Nguyên Tắc Config

Config phải tối giản và phục vụ đúng concept:

```text
Camera nào nhìn slot nào, slot đó detect object gì, polygon ở đâu.
```

Không đưa mapping FMS/HIK/WMS vào config chính nếu Tablet chưa cần.

## 2. `configs/cameras.json`

Đề xuất:

```json
[
  {
    "camera_id": 1,
    "camera_key": "cam1",
    "name": "Camera 1",
    "source_type": "rtsp",
    "source_path": "rtsp://user:password@192.168.11.1:554/Streaming/Channels/101",
    "model_path": "weights/best.pt",
    "slot_config": "configs/slots_cam1.json",
    "enabled": true
  }
]
```

### Field Rules

- `camera_id`: ID public gửi cho Tablet, ưu tiên số nguyên.
- `camera_key`: ID nội bộ nếu code cũ đang dùng dạng `"cam1"`.
- `name`: tên hiển thị/debug.
- `source_type`: `rtsp`, `live`, hoặc `video`.
- `source_path`: RTSP/video path.
- `model_path`: model detect.
- `slot_config`: file ROI slot.
- `enabled`: bật/tắt camera.

## 3. `configs/slots_camX.json`

Đề xuất:

```json
{
  "camera_id": 1,
  "camera_key": "cam1",
  "source": "calibration/cam1_reference.jpg",
  "slots": [
    {
      "slot_id": 1,
      "name": "Slot 1",
      "target_object": "car",
      "polygon": [
        [0.10, 0.20],
        [0.30, 0.20],
        [0.30, 0.45],
        [0.10, 0.45]
      ],
      "spatial_method": "bbox_intersects",
      "enabled": true
    }
  ]
}
```

### Field Rules

- `slot_id`: ID public gửi cho Tablet.
- `name`: optional, phục vụ debug.
- `target_object`: class model cần detect để xác định `Occupied`.
- `polygon`: normalized coordinate `[0..1]`.
- `spatial_method`: optional override, mặc định lấy từ rules.
- `enabled`: bật/tắt slot.

Trong phase chính, không bắt buộc có:

- `storageBinCode`
- `ctnr_typ`
- `position_code`
- `stg_bin_code`

## 4. `configs/rules.json`

Đề xuất production CPU:

```json
{
  "spatial_method": "bbox_intersects",
  "enter_window": 3,
  "enter_count": 2,
  "exit_window": 7,
  "exit_count": 5,
  "unknown_timeout_sec": 3.0,
  "conf_threshold": 0.5,
  "img_size": 416,
  "batch_size": 1,
  "batch_timeout_ms": 0,
  "max_pending_requests": 6
}
```

Ý nghĩa:

- `enter_*`: chuyển sang `Occupied`.
- `exit_*`: chuyển sang `Empty`.
- `unknown_timeout_sec`: quá thời gian không có observation mới thì `Unknown`.

## 5. `configs/runtime.json`

Đề xuất:

```json
{
  "decode_fps_default": 6.0,
  "slot_infer_fps_default": 2.0,
  "websocket_push_fps": 3.0,
  "export_interval_ms": 500,
  "debug_export_fps": 2.0,
  "schedule_sleep_ms": 5,
  "preview_width": 960,
  "preview_height": 540,
  "server": {
    "host": "0.0.0.0",
    "port": 8088,
    "websocket_path": "/ws/slot-states",
    "rest_enabled": true
  }
}
```

## 6. `configs/ingest.json`

Đề xuất:

```json
{
  "stream_profile": "sub",
  "latest_frame_only": true,
  "reader_output_fps": 6.0,
  "expected_source_fps": 25.0,
  "buffer_size": 1,
  "reconnect_delay_sec": 1.0,
  "rtsp_transport": "tcp",
  "open_timeout_msec": 2000,
  "read_timeout_msec": 1000,
  "skip_sleep_ms": 2
}
```

Nếu sub-stream không đủ rõ, đổi sang main-stream nhưng cần giảm inference FPS hoặc image size.

## 7. Config Validation

Runtime phải fail fast khi:

- Trùng `camera_id`.
- Trùng `camera_key`.
- Thiếu `slot_config`.
- Trùng `slot_id` trong cùng camera.
- Thiếu `target_object`.
- Polygon không hợp lệ.
- Model path không tồn tại.
- Camera enabled nhưng source invalid.

Không được publish `Empty` cho slot có config lỗi.

## 8. Optional Future Mapping

Nếu sau này server tổng cần mapping warehouse/FMS, thêm file riêng:

```text
configs/integration_mapping.json
```

Không trộn vào config slot chính nếu chưa cần.

Ví dụ optional:

```json
{
  "items": [
    {
      "camera_id": 1,
      "slot_id": 2,
      "nodeStore": "B03",
      "storageBinCode": "B03"
    }
  ]
}
```

