# Current State Report

## 1. Tong Tat

Project HAMAS25018 hien da duoc tinh gon ve dung mot muc tieu:

```text
Vision Server doc camera -> suy luan slot state -> push cho Tablet -> Tablet validate -> FMS nhan task.
```

Project khong con giu cac luong thua nhu elevator, HIK bridge, AGV control noi bo hay frontend monitor legacy trong runtime chinh.

## 2. Hien Tai Trong Repo Co Gi

### Runtime Chinh

- [app/main_vision_server.py](/C:/Users/longn/PyCharmMiscProject/HAMAS25018/app/main_vision_server.py)
- [core/vision_runtime.py](/C:/Users/longn/PyCharmMiscProject/HAMAS25018/core/vision_runtime.py)
- [core/websocket_server.py](/C:/Users/longn/PyCharmMiscProject/HAMAS25018/core/websocket_server.py)
- [core/slot_state_store.py](/C:/Users/longn/PyCharmMiscProject/HAMAS25018/core/slot_state_store.py)
- [core/slot_contract.py](/C:/Users/longn/PyCharmMiscProject/HAMAS25018/core/slot_contract.py)

### Vision Core

- `core/camera_reader.py`
- `core/video_file_reader.py`
- `core/frame_store.py`
- `core/detector.py`
- `core/model_registry.py`
- `core/inference_scheduler.py`
- `core/zone_reasoner.py`
- `core/state_tracker.py`
- `core/geometry.py`

### Config

- `configs/cameras.json`
- `configs/ingest.json`
- `configs/rules.json`
- `configs/runtime.json`
- `configs/zones_cam1.json` den `configs/zones_cam6.json`

### Docs

- `docs/README.md`
- `docs/01_project_spec.md`
- `docs/02_system_architecture.md`
- `docs/03_data_contract_api.md`
- `docs/04_config_spec.md`
- `docs/05_migration_scope.md`
- `docs/06_cpu_runtime_plan.md`
- `docs/07_testing_acceptance.md`
- `docs/08_deployment_operations.md`
- `docs/09_risk_register.md`
- `docs/10_implementation_backlog.md`
- `docs/11_checkpoint_plan.md`
- `docs/12_operation_runbook.md`

## 3. Da Tinh Gon Nhung Gi

Da loai khoi runtime chinh:

- Elevator process.
- HIK RCS direct bridge.
- AGV control/export cu.
- GUI frontend cu.
- Replay runtime cu.
- Legacy supervisor script cu.
- PyQt6 dependency.

## 4. He Thong Dang Lam Gi

Vision Server hien lam dung cac viec sau:

1. Doc RTSP hoac video source.
2. Giu latest frame cho tung camera.
3. Chay detector CPU-only.
4. Quy detection vao ROI/slot.
5. Sinh state `Empty / Occupied / Unknown`.
6. Giu state moi nhat trong memory.
7. Broadcast snapshot qua WebSocket.
8. Tra REST health va snapshot de debug/fallback.
9. Ghi log state change va snapshot runtime.

## 5. Cach Vision Lam Viec Voi Tablet

### Kenh Chinh

```text
WebSocket /ws/slot-states
```

### Flow

1. Tablet connect vao Vision Server.
2. Vision gui snapshot dau tien ngay khi connect.
3. Vision tiep tuc push snapshot dinh ky.
4. Tablet hien thi trang thai real-time.
5. User chon thao tac tren Tablet.
6. Tablet validate slot state truoc khi gui task len FMS.

### Rule Quan Trong

- `Empty`: co the hop le cho Store tuy business rule cua Tablet.
- `Occupied`: canh bao neu Store vao slot nay.
- `Unknown`: fail-safe, khong coi la `Empty`.

## 6. Cach Van Hanh

### Khoi Dong

```bash
python app/main_vision_server.py
```

### Check Nhanh

- `GET /health`
- `GET /api/v1/slots`
- WebSocket connect `/ws/slot-states`

### Khi Camera Loi

- Vision khong chet theo mot camera.
- Slot thuoc camera do chuyen `Unknown`.
- Operator xu ly camera/source/ROI rieng.

## 7. Nhung Phan Con Cho Dau Vao Tu Ban

- Model weights da train xong.
- Polygon ROI chinh xac cho tung camera.
- Class mapping detector cuoi cung neu co chinh.

## 8. Hien Trang San Sang Den Muc NaO

He thong hien da san cho:

- Hoan thien model weights.
- Cam ROI that.
- Test replay/live source.
- Connect Tablet.
- Chay kiem thu thuc dia.

Chua nen xem la production hoan chinh neu chua:

- Co weights that.
- Co ROI that.
- Co test live voi camera thuc.
- Co burn-in thuc te.

## 9. Ket Luan

Repo hien da duoc do ve dung loi Vision Server. Phan con lai la cam model/ROI that va thuc nghiem voi Tablet de chot van hanh.

