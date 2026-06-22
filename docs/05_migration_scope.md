# Migration Scope From Current Core

## 1. Mục Tiêu Migration

Refactor project hiện tại thành Vision Server tối giản theo concept:

```text
Camera -> Slot State -> WebSocket -> Tablet
```

Không viết lại toàn bộ core. Giữ pipeline hữu ích, bỏ nghiệp vụ thừa.

## 2. Giữ Lại

### Camera/Core Runtime

- `core/camera_reader.py`
- `core/video_file_reader.py`
- `core/frame_store.py`
- `core/model_registry.py`
- `core/inference_runtime.py`
- `core/geometry.py`
- `core/file_utils.py`
- `core/path_utils.py`
- `core/logger_config.py`
- `core/runtime_maintenance.py`

### Vision Logic Có Thể Tái Dùng

- `core/zone_reasoner.py` đổi ý nghĩa thành slot reasoner hoặc bọc lại.
- `core/state_tracker.py` giữ hysteresis, đổi output state label.
- `core/visualizer.py` giữ cho debug frame.
- `core/history_logger.py` giữ log state change.

### Tools Optional

- `tools/roi_designer.py`
- `tools/capture_frame.py`
- Replay tools nếu cần test.

## 3. Loại Khỏi Main Runtime

### Elevator

Loại khỏi runtime chính:

- `core/elevator_runtime.py`
- `core/elevator_state_machine.py`
- `core/elevator_types.py`
- `configs/elevator.json`
- `tools/elevator_cmd.py`
- Mọi logic `camera_type = elevator`.

### HIK/RCS Direct Bridge

Không import/chạy trong runtime chính:

- `core/hik_rcs_bridge.py`
- `core/hik_rcs_client.py`
- `core/hik_callback_server.py`
- `configs/hik_rcs.json`
- `tools/hik_rcs_cli.py`

Các file có thể giữ tham khảo, nhưng không thuộc main concept.

### AGV/FMS Dispatch

Vision không gửi:

- `POST /sendTask`
- bind/unbind request
- task command
- AGV control command

Tablet mới là bên gửi task lên FMS.

## 4. Đổi Tên Khái Niệm

Khái niệm cũ:

```text
zone / warehouse bin / AGV answer
```

Khái niệm mới:

```text
slot / slot state / tablet payload
```

Mapping code có thể làm dần:

- `ZoneConfig` -> `SlotConfig` hoặc giữ `ZoneConfig` nội bộ nhưng export là slot.
- `ZoneObservation` -> `SlotObservation`.
- `ZoneState` -> `SlotState`.
- `agv_latest.json` -> `slot_states_latest.json`.

## 5. Module Mới Đề Xuất

```text
core/slot_contract.py
core/slot_state_store.py
core/websocket_server.py
core/slot_exporter.py
app/main_vision_server.py
```

### `slot_contract.py`

Chịu trách nhiệm build payload:

- `Empty`
- `Occupied`
- `Unknown`
- timestamp
- total_slots
- slots list

### `slot_state_store.py`

Thread-safe store:

- update state theo `camera_id + slot_id`.
- get snapshot.
- get camera health.
- track last_changed_at nội bộ.

### `websocket_server.py`

Broadcast snapshot cho Tablet.

Không trigger inference. Chỉ đọc từ state store.

### `slot_exporter.py`

Ghi snapshot/debug file:

- `outputs/runtime/slot_states_latest.json`
- per-camera snapshot nếu cần.
- history state changes.

## 6. Main Runtime Refactor

Từ `mainProcess.py`, cần bỏ:

- `ElevatorRuntime`.
- `HikRcsBridge`.
- `_build_control_payload`.
- `_elevator_zone_payload_from_snapshot`.
- `_schedule_hik_sync`.
- `_export_agv_snapshot`.
- `elevators` trong process snapshot.

Thêm:

- Slot contract builder.
- Slot state store.
- WebSocket broadcast loop/server.
- REST health tối giản.

## 7. Config Migration

Từ `configs/zones_camX.json` hiện tại:

```json
{
  "zone_id": "A1",
  "target_object": "pallet",
  "polygon": [...]
}
```

Sang:

```json
{
  "slot_id": 1,
  "name": "Slot 1",
  "target_object": "car",
  "polygon": [...],
  "enabled": true
}
```

Nếu Tablet đang dùng layout theo `slot_id`, ưu tiên map rõ `slot_id` đúng với UI.

## 8. Migration Phases

### Phase 1: Docs And Contract Freeze

Chốt bộ docs này với Tablet/FMS team.

### Phase 2: Slot Config Schema

Sửa dataclass/config loader theo camera/slot.

### Phase 3: Slot State Contract

Build payload đúng WebSocket contract.

### Phase 4: Runtime Cleanup

Gỡ elevator/HIK/FMS coupling.

### Phase 5: WebSocket Server

Push snapshot cho Tablet.

### Phase 6: REST/Debug Snapshot

Health và debug endpoint tối giản.

### Phase 7: Test With Tablet

Tablet nhận WebSocket, validate slot, gửi task FMS.

