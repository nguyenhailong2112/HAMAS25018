# Implementation Backlog

## Phase 0: Freeze Concept And Contract

Deliverables:

- Bộ docs hiện tại.
- Chốt `camera_id` public với Tablet.
- Chốt `slot_id` public với Tablet.
- Chốt 3 state: `Empty`, `Occupied`, `Unknown`.
- Chốt WebSocket endpoint.
- Chốt Tablet sẽ dùng full snapshot payload.

Exit criteria:

- Tablet team đọc được payload và xác nhận parse được.
- FMS team xác nhận Vision không gọi FMS.
- Không còn yêu cầu HIK/elevator/server tổng trong phase chính.

## Phase 1: Slot Config Schema

Tasks:

- Sửa `CameraConfig` để có `camera_id` public và `camera_key` nội bộ nếu cần.
- Tạo/đổi `SlotConfig`.
- Load `configs/slots_camX.json`.
- Validate `slot_id`, `target_object`, polygon.
- Update sample config.

Files dự kiến:

- `core/types.py`
- `core/config.py`
- `configs/cameras.json`
- `configs/slots_cam*.json`

## Phase 2: Slot Contract

Tasks:

- Tạo `core/slot_contract.py`.
- Map internal state sang public label:
  - occupied -> `Occupied`
  - empty -> `Empty`
  - unknown -> `Unknown`
- Build WebSocket snapshot:
  - `timestamp`
  - `total_slots`
  - `slots`
- Giữ payload tối giản.

Files dự kiến:

- `core/slot_contract.py`
- `core/types.py`

## Phase 3: Slot State Store

Tasks:

- Tạo thread-safe store.
- Key theo `camera_id + slot_id`.
- Update state từ tracker.
- Snapshot toàn bộ slots.
- Track camera health nội bộ.
- Track last update nội bộ.

Files dự kiến:

- `core/slot_state_store.py`

## Phase 4: Runtime Cleanup

Tasks:

- Gỡ elevator khỏi runtime chính.
- Gỡ HIK bridge khỏi runtime chính.
- Gỡ AGV/HIK export.
- Đổi process snapshot sang slot snapshot.
- Giữ debug preview nếu cần.

Files dự kiến:

- `mainProcess.py` hoặc `app/main_vision_server.py`
- `core/runtime_bridge.py`

## Phase 5: WebSocket Server

Tasks:

- Tạo WebSocket endpoint `/ws/slot-states`.
- Broadcast full snapshot 2-5 Hz.
- Gửi snapshot ngay khi client connect.
- Log client connect/disconnect.
- Không trigger inference từ client.

Files dự kiến:

- `core/websocket_server.py`
- `app/main_vision_server.py`
- `requirements.txt` nếu cần dependency WebSocket.

Dependency note:

- Nếu dùng FastAPI/Uvicorn/WebSocket: code sạch hơn nhưng cần thêm package.
- Nếu muốn tối thiểu dependency: dùng thư viện nhẹ hoặc stdlib cho REST, nhưng WebSocket stdlib không tiện.

Quyết định dependency nên dựa vào môi trường deploy thực tế.

## Phase 6: REST And Snapshot Debug

Tasks:

- `GET /health`.
- `GET /api/v1/slots`.
- `GET /api/v1/cameras`.
- Export `outputs/runtime/slot_states_latest.json`.
- Export history state changes.

Files dự kiến:

- `core/slot_exporter.py`
- `core/websocket_server.py` hoặc `core/api_server.py`

## Phase 7: CPU Runtime Tuning

Tasks:

- Đặt CPU-only default.
- Decode FPS 5-8.
- Infer FPS 1-3.
- Batch size 1.
- Unknown timeout hợp lý.
- Log detect ms/camera.

Files dự kiến:

- `configs/rules.json`
- `configs/runtime.json`
- `configs/ingest.json`
- runtime main file.

## Phase 8: Tablet Integration Test

Tasks:

- Tablet connect WebSocket.
- Verify payload parse.
- Verify UI update.
- Test slot `Empty`.
- Test slot `Occupied`.
- Test slot `Unknown`.
- Test Tablet warning modal.
- Test Tablet sends `POST /sendTask` to FMS.

Vision success criteria:

- Vision push đúng state.
- Vision không gọi FMS.

## Phase 9: Production Deployment

Tasks:

- Setup run script/service/watchdog.
- Setup production config.
- Test camera reconnect.
- Test WebSocket reconnect.
- Burn-in 24h.
- Backup config.
- Handover operation guide.

## Suggested First Coding Order

1. Update config schema camera/slot.
2. Build slot contract.
3. Build slot state store.
4. Refactor runtime remove elevator/HIK.
5. Export slot snapshot.
6. Add WebSocket server.
7. Add REST health/debug.
8. Test with replay.
9. Test with Tablet.
10. Tune CPU and burn-in.

Nguyên tắc xuyên suốt:

```text
Không thêm module nếu main concept chưa cần.
Không đưa business rule vào Vision.
Không làm payload phức tạp khi Tablet chỉ cần camera_id, slot_id, state.
```

