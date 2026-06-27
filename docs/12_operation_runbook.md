# Operation Runbook

## 1. Muc Dich

Tai lieu nay la checklist van hanh ngan cho ngay chay that.

Muc tieu:

- Khoi dong Vision Server dung thu tu.
- Xac nhan WebSocket/API song.
- Xac nhan Tablet doc duoc trang thai.
- Xac nhan camera va model da san sang.

## 2. Dieu Kien Truoc Khi Chay

- `weights/best.pt` da duoc dat dung duong dan.
- `configs/cameras.json` da co du 6 camera.
- `configs/zones_cam1.json` den `configs/zones_cam6.json` da duoc ve ROI.
- Camera RTSP reachable.
- May co quyen doc/write thu muc project.

## 3. Cau Hinh Hien Tai

- Camera 1 den 5: object muc tieu `pallet`.
- Camera 6: object muc tieu `trolley`.
- WebSocket: `/ws/slot-states`.
- REST health: `/health`.
- REST snapshot: `/api/v1/slots`.

## 4. Thu Tu Chay

1. Kiem tra `weights/best.pt`.
2. Kiem tra 6 file ROI `configs/zones_cam*.json`.
3. Khoi dong Vision Server:

```bash
python app/main_vision_server.py
```

4. Mo Tablet va connect WebSocket.
5. Xac nhan state `Unknown` ban dau xuat hien cho toan bo slot.
6. Dat camera vao vung thuc te hoac replay source test.
7. Xac nhan state chuyen sang `Empty` hoac `Occupied`.

## 5. Kiem Tra Nhanh Khi Server Da Len

### Health Check

Goi:

```text
GET /health
```

Ky vong:

- `status = online`
- `camera_count = 6`
- `total_slots` dung theo so ROI da cau hinh

### Snapshot Check

Goi:

```text
GET /api/v1/slots
```

Ky vong:

- Co danh sach `slots`.
- Moi slot co `camera_id`, `slot_id`, `state`.

### WebSocket Check

Connect vao:

```text
ws://VISION_SERVER_IP:2112/ws/slot-states
```

Ky vong:

- Nhan snapshot dau tien ngay khi connect.
- Nhan update dinh ky.

## 6. Loi Thuong Gap

- Khong thay camera: kiem tra RTSP source.
- Toan `Unknown`: kiem tra model, ROI, nguong confidence, hoac source chua co frame.
- WebSocket khong len: kiem tra port, firewall, va process dang chay.
- State khong doi: kiem tra class name model co khop `target_object` khong.

## 7. Quy Tac Van Hanh

- Khong chinh ROI truc tiep khi chua co anh reference va test xac nhan.
- Khong coi `Unknown` la `Empty`.
- Khong dung Vision Server neu chi mot camera loi, tru khi loi lan rong.
- Khi doi model hoac ROI, phai chay lai health check va snapshot check.

