# Deployment And Operations

## 1. Mục Tiêu Vận Hành

Vision Server chạy 24/7 như cảm biến ngoại vi cho Tablet.

Yêu cầu:

- Tự khởi động.
- Tự reconnect camera.
- Push WebSocket ổn định.
- Có health check.
- Có log và snapshot debug.
- Không cần operator can thiệp thường xuyên.

## 2. Runtime Production

Entrypoint sau refactor:

```text
python app/main_vision_server.py
```

Trong phase chuyển đổi có thể vẫn dùng:

```text
python mainProcess.py
```

nhưng mục tiêu cuối là runtime tên rõ theo concept mới.

## 3. Network

Vision Server expose:

```text
ws://VISION_SERVER_IP:8088/ws/slot-states
http://VISION_SERVER_IP:8088/health
http://VISION_SERVER_IP:8088/api/v1/slots
```

Tablet là client chính.

FMS không cần connect Vision trong phase chính.

Server tổng sau này nếu cần có thể đọc REST hoặc WebSocket mà không thay đổi core.

## 4. Output Runtime

Đề xuất:

```text
outputs/runtime/slot_states_latest.json
outputs/runtime/cameras/{camera_id}.json
outputs/runtime/preview/{camera_id}.jpg
outputs/runtime/debug/{camera_id}.jpg
outputs/history/slot_state_changes.jsonl
outputs/logs/runtime.log
```

## 5. Logging

Log cần có:

- Runtime start/stop.
- Config loaded.
- Model loaded.
- WebSocket server started.
- Tablet connected/disconnected.
- Camera connected/offline/reconnected.
- State transition.
- Unknown timeout.
- Inference error.

Log không cần:

- Business task detail của FMS.
- User operation detail trên Tablet.
- Mapping WMS/WCS nếu Vision không dùng.

## 6. Health Monitoring

`GET /health` phải đủ để biết:

- Vision process online.
- Camera count.
- Online camera count.
- Total slots.
- Unknown slots.
- Uptime.

Tablet nên hiển thị cảnh báo nếu:

- WebSocket mất kết nối.
- Vision health offline.
- Slot critical đang `Unknown`.

## 7. Recovery

### Camera Offline

Vision:

- Reconnect.
- Slot thuộc camera chuyển `Unknown`.

Tablet:

- Hiện state `Unknown`.
- Cảnh báo nếu user thao tác liên quan.

### Vision Server Down

Tablet:

- Mất WebSocket.
- Hiển thị trạng thái mất kết nối Vision.
- Không nên âm thầm coi slot là `Empty`.

### FMS Error

Không thuộc Vision. Tablet xử lý response từ FMS và alert user.

## 8. Deployment Checklist

- Cài dependency.
- Check camera RTSP.
- Check model path.
- Check slot config.
- Start Vision Server.
- Check `/health`.
- Check WebSocket bằng Tablet/tool.
- Check snapshot file.
- Test camera disconnect.
- Setup watchdog/service.
- Burn-in.

## 9. Change Management

Mỗi lần đổi config nên ghi:

- Ngày giờ.
- Camera/slot nào đổi.
- Người đổi.
- Lý do.
- Test đã chạy.
- Config backup.

Không chỉnh ROI trực tiếp trên production nếu chưa có ảnh reference và test xác nhận.

