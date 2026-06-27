# Site Communication Guide

Tai lieu nay dung de lam viec truc tiep voi team Tablet, FMS/WCS, server tong va team network khi trien khai tai site.

## 1. Vai Tro Cua Vision Server

Vision Server la mot server ngoai vi, dong vai tro nhu cam bien thong minh cho tung vi tri luu tru hang.

Vision Server lam:

- Doc stream camera CCTV.
- Chay object detection.
- Kiem tra object co nam trong ROI/slot hay khong.
- Ket luan trang thai moi slot.
- Luu state moi nhat trong bo nho runtime.
- Ghi snapshot ra file noi bo.
- Push state lien tuc qua WebSocket cho Tablet/server khac.
- Cung cap REST API de health check, debug va lay snapshot.

Vision Server khong lam:

- Khong tao task AGV/FMR.
- Khong goi FMS.
- Khong quyet dinh business rule dieu phoi.
- Khong thay Tablet xac nhan lenh nguoi dung.

## 2. Trang Thai Vision Tra Ra

Moi slot chi co 3 state public:

| State | Y nghia | Tablet/FMS nen xu ly |
| --- | --- | --- |
| `Empty` | Vision dang thay slot khong co target object | Co the coi la vi tri trong, neu business rule cho phep |
| `Occupied` | Vision dang thay slot co target object | Co hang / bind / occupied |
| `Unknown` | Vision chua du chac chan, camera stale, moi start, hoac pipeline dang loi | Khong duoc coi la `Empty`; nen canh bao hoac chan thao tac |

Object target theo config hien tai:

- `cam1` den `cam5`: `pallet`.
- `cam6`: `trolley`.

Tong ROI skeleton hien tai:

- `cam1`: 7 slot.
- `cam2`: 3 slot.
- `cam3`: 2 slot.
- `cam4`: 4 slot.
- `cam5`: 4 slot.
- `cam6`: 2 slot.

Tong cong: 22 slot.

## 3. Dia Chi Ket Noi

PC Vision Server can dat IP tinh trong dai site:

```text
192.168.53.xxx
```

Vi du neu PC Vision la `192.168.53.50`, cac team khac dung:

```text
Base URL:  http://192.168.53.50:8088
WebSocket: ws://192.168.53.50:8088/ws/slot-states
Monitor:   http://192.168.53.50:8088/monitor
```

Port mac dinh:

```text
8088/TCP
```

## 4. Mo Port Tren Windows Server Vision

Neu Windows Firewall dang bat, can allow inbound TCP port `8088`.

Lenh goi y cho IT/network team chay bang Administrator PowerShell:

```powershell
New-NetFirewallRule -DisplayName "HAMAS25018 Vision Server 8088" -Direction Inbound -Protocol TCP -LocalPort 8088 -Action Allow
```

Kiem tra port dang listen:

```powershell
netstat -ano | findstr :8088
```

Ky vong thay trang thai:

```text
LISTENING
```

## 5. Cau Hinh IP Allowlist

File:

```text
configs/runtime.json
```

Cho phep tat ca client noi bo:

```json
{
  "server": {
    "host": "192.168.53.xxx",
    "port": 8088,
    "websocket_path": "/ws/slot-states",
    "rest_enabled": true,
    "ip_allowlist": []
  }
}
```

Chi cho phep mot vai IP:

```json
{
  "server": {
    "ip_allowlist": [
      "192.168.53.10",
      "192.168.53.20"
    ]
  }
}
```

Cho phep ca subnet site:

```json
{
  "server": {
    "ip_allowlist": [
      "192.168.53.0/24"
    ]
  }
}
```

Neu client khong nam trong allowlist, Vision Server tra HTTP `403`:

```json
{
  "error": {
    "code": "client_ip_not_allowed",
    "message": "Client IP is not in Vision Server allowlist.",
    "client_ip": "192.168.53.99"
  }
}
```

## 6. REST API Cho Kiem Tra Nhanh

### 6.1 Health Check

Dung de biet Vision Server da chay va runtime con song khong.

```text
GET http://VISION_SERVER_IP:8088/health
```

Vi du:

```bash
curl http://192.168.53.50:8088/health
```

Response mau:

```json
{
  "status": "online",
  "timestamp": "2026-06-23T09:00:00.000+07:00",
  "uptime_sec": 120.5,
  "camera_count": 6,
  "online_camera_count": 6,
  "total_slots": 22,
  "unknown_slots": 0
}
```

Ket noi thanh cong khi:

- HTTP status la `200`.
- `status` la `online`.
- `camera_count` dung so camera cau hinh.
- `total_slots` dung so ROI cau hinh.

### 6.2 Server Info

Dung de team Tablet/FMS tu doc endpoint va contract hien tai.

```text
GET http://VISION_SERVER_IP:8088/api/v1/server-info
```

Response mau:

```json
{
  "service": "HAMAS25018 Vision Server",
  "role": "Occupancy Sensor Server",
  "endpoints": {
    "health": "/health",
    "server_info": "/api/v1/server-info",
    "slots_snapshot": "/api/v1/slots",
    "cameras": "/api/v1/cameras",
    "websocket_slots": "/ws/slot-states",
    "monitor": "/monitor"
  },
  "slot_contract": {
    "states": ["Empty", "Occupied", "Unknown"],
    "required_fields": ["nodeName", "state"],
    "unknown_rule": "Unknown must not be treated as Empty."
  }
}
```

### 6.3 Slot Snapshot

Dung de lay state moi nhat mot lan qua HTTP.

```text
GET http://VISION_SERVER_IP:8088/api/v1/slots
```

Response mau:

```json
{
  "timestamp": "2026-06-23T09:00:01.123+07:00",
  "total_slots": 22,
  "slots": [
    {
      "nodeName": "predock_oil_2",
      "state": "Empty"
    },
    {
      "nodeName": "predock_oil_3",
      "state": "Occupied"
    },
    {
      "nodeName": "drop_kho_5",
      "state": "Unknown"
    }
  ],
  "camera_count": 6,
  "online_camera_count": 6,
  "camera_meta": [
    {
      "camera_id": "cam1",
      "camera_name": "Camera 1",
      "timestamp": 1782147601.123,
      "health": "online",
      "detect_ms": 83.5,
      "frame_id": 128,
      "slot_count": 7
    }
  ]
}
```

Team Tablet co the dung API nay lam fallback neu WebSocket mat ket noi tam thoi.

### 6.4 Camera Summary

Dung de debug camera nao dang online/offline.

```text
GET http://VISION_SERVER_IP:8088/api/v1/cameras
```

## 7. WebSocket Realtime Cho Tablet

Kenh chinh:

```text
ws://VISION_SERVER_IP:8088/ws/slot-states
```

Vision Server se:

- Gui snapshot dau tien ngay sau khi client connect thanh cong.
- Push snapshot dinh ky theo `websocket_push_fps`.
- Mac dinh hien tai push 5 lan/giay.

Payload WebSocket giong `GET /api/v1/slots`.

Client Tablet nen lam:

1. Connect WebSocket.
2. Nhan message JSON dau tien.
3. Parse `slots`.
4. Luu latest state theo key `nodeName`.
5. Neu WebSocket mat ket noi, retry sau 1-3 giay.
6. Trong luc retry, co the goi `GET /api/v1/slots` de lay snapshot fallback.

## 8. Test Bang Postman

Postman test REST:

1. Chon method `GET`.
2. Nhap URL:

```text
http://192.168.53.50:8088/health
```

3. Bam Send.
4. Thanh cong khi status code `200` va body la JSON.

Postman test WebSocket:

1. New request.
2. Chon `WebSocket`.
3. Nhap URL:

```text
ws://192.168.53.50:8088/ws/slot-states
```

4. Bam Connect.
5. Thanh cong khi Postman hien `Connected` va nhan JSON snapshot dau tien.

## 9. Test Bang Lenh Don Gian

Tu may Tablet/server khac, ping PC Vision:

```powershell
ping 192.168.53.50
```

Kiem tra port:

```powershell
Test-NetConnection 192.168.53.50 -Port 8088
```

Thanh cong khi:

```text
TcpTestSucceeded : True
```

Kiem tra REST:

```powershell
Invoke-RestMethod http://192.168.53.50:8088/health
```

## 10. Monitor Cho Nguoi Van Hanh

Mo tren trinh duyet:

```text
http://VISION_SERVER_IP:8088/monitor
```

Man hinh nay hien:

- Tong so slot.
- So slot `Empty`.
- So slot `Occupied`.
- So slot `Unknown`.
- Tung camera.
- Health camera.
- Frame id moi nhat.
- Thoi gian inference `detect_ms`.

## 11. Logs Va Output Noi Bo

Snapshot moi nhat:

```text
outputs/runtime/slot_states_latest.json
```

Lich su doi state:

```text
outputs/history/slot_state_changes.jsonl
```

Moi dong JSONL la mot lan state thay doi. File nay dung de truy vet sau khi test site.

## 12. Checklist Ban Giao Cho Team Tablet

Can dua cho team Tablet:

- Vision Server IP.
- Port `8088`.
- WebSocket path `/ws/slot-states`.
- REST fallback `/api/v1/slots`.
- Health endpoint `/health`.
- Server info endpoint `/api/v1/server-info`.
- 3 state hop le: `Empty`, `Occupied`, `Unknown`.
- Quy tac: `Unknown` khong duoc xu ly nhu `Empty`.
- Danh sach `nodeName` chinh thuc sau khi ROI final.

## 13. Checklist Ban Giao Cho Team Network/IT

Can thong nhat:

- PC Vision dat IP tinh trong dai `192.168.53.xxx`.
- Tablet/FMS/server tong ping duoc PC Vision.
- TCP port `8088` inbound duoc allow.
- Neu dung allowlist, cung cap IP client chinh xac.
- Neu qua VLAN/routing, mo route giua client subnet va Vision subnet.

## 14. Khi Nao Goi La Ket Noi Thanh Cong

REST thanh cong khi:

- Ping hoac route toi PC Vision OK.
- `Test-NetConnection IP -Port 8088` tra `TcpTestSucceeded: True`.
- `GET /health` tra HTTP `200`.
- `GET /api/v1/server-info` tra dung contract.
- `GET /api/v1/slots` co danh sach slot.

WebSocket thanh cong khi:

- Client connect duoc `ws://IP:8088/ws/slot-states`.
- Nhan JSON snapshot dau tien ngay sau khi connect.
- Tiep tuc nhan update dinh ky.
- Khi thay doi hang trong ROI, state slot doi theo sau hysteresis window.

## 15. Neu Ket Noi That Bai

| Hien tuong | Nguyen nhan thuong gap | Cach kiem tra |
| --- | --- | --- |
| Ping fail | Sai IP, sai subnet, VLAN/route chua mo | `ipconfig`, `ping`, switch/VLAN |
| Port fail | Server chua chay hoac firewall chan | `netstat -ano`, `Test-NetConnection` |
| HTTP 403 | Client khong nam trong allowlist | Kiem tra `configs/runtime.json` |
| HTTP 404 | Sai path API | Goi `/api/v1/server-info` de xem endpoint |
| WebSocket connect fail | Sai `ws://`, sai port, firewall, allowlist | Test bang Postman WebSocket |
| Toan `Unknown` | Camera/model/ROI chua san sang | Mo `/monitor`, xem `camera_meta` |
| Camera offline | RTSP/IP camera loi | Kiem tra `configs/cameras.json` va ping camera |

## 16. Callback Va Notify

Concept hien tai khong dung callback nguoc sang Tablet/FMS.

Ly do:

- Vision la state provider.
- Tablet/server ngoai la consumer.
- WebSocket da la kenh push realtime.
- REST snapshot la fallback.

Neu sau nay server tong muon callback rieng, nen them sau theo mot endpoint config rieng. Hien tai khong can de giu he thong don gian, ro rang va de van hanh.
