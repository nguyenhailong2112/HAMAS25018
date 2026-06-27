# Checkpoint Plan

## Checkpoint 0: Freeze Scope

- Confirm Vision is sensor server only.
- Confirm Tablet is business validation layer.
- Confirm FMS is execution layer.
- Confirm `Empty / Occupied / Unknown` is final public state set.

## Checkpoint 1: Config Readiness

- 6 camera configs load được.
- Mỗi camera có ROI/slot config hợp lệ.
- `target_object` hoặc `target_objects` đã chốt.
- Camera 1-5 map `pallet`.
- Camera 6 map `trolley`.
- Model weights đã đặt đúng thư mục chương trình.

## Checkpoint 2: Detection Integration

- Detector trả detections ổn định.
- Class mapping đúng:
  - `pallet`
  - `trolley`
  - `person`
  - `obstacle`
  - `FMR`

## Checkpoint 3: State Pipeline

- Detection -> slot observation.
- Slot observation -> hysteresis state.
- State -> `Empty / Occupied / Unknown`.
- Unknown timeout hoạt động đúng.

## Checkpoint 4: API And WebSocket

- WebSocket `/ws/slot-states` trả snapshot đúng.
- REST `/health` hoạt động.
- REST `/api/v1/slots` hoạt động.
- Tablet parse được payload.
- Snapshot ban đầu đã có đầy đủ slot `Unknown`.

## Checkpoint 5: Operation Hardening

- Camera offline không làm crash process.
- Reconnect hoạt động.
- Snapshot file được ghi.
- Log rotation hoạt động.
- Burn-in 24h đạt.
