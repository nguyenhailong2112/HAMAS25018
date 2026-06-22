# Testing And Acceptance Plan

## 1. Mục Tiêu Test

Test phải chứng minh:

- Vision detect đúng state slot.
- WebSocket payload đúng contract.
- Tablet nhận được state real-time.
- `Unknown` hoạt động đúng khi lỗi/stale.
- Runtime CPU-only chạy ổn định.

## 2. Test Levels

### 2.1 Unit Test

Nên test:

- Config loader camera/slot.
- Polygon validation.
- State mapping sang `Empty`, `Occupied`, `Unknown`.
- Hysteresis enter/exit.
- Unknown timeout.
- WebSocket payload builder.

### 2.2 Offline Vision Test

Dùng video/image replay:

- Slot trống.
- Slot có hàng.
- Object ngoài ROI.
- Object che khuất một phần.
- Ánh sáng xấu.
- Motion blur.
- Camera/frame stale giả lập.

Expected:

- Có object ổn định -> `Occupied`.
- Không object ổn định -> `Empty`.
- Không đủ dữ liệu -> `Unknown`.

### 2.3 Integration Test With Tablet

Test trực tiếp:

1. Tablet connect WebSocket.
2. Vision push snapshot.
3. Tablet update UI.
4. User trigger Store/Pick/Cycle.
5. Tablet validate slot state.
6. Tablet hiện warning khi slot không hợp lệ.
7. Tablet gửi task FMS khi user xác nhận.

Vision không cần gọi FMS trong test này.

### 2.4 Runtime Test

Chạy 6 camera/source:

- WebSocket push không ngắt.
- REST `/health` trả đúng.
- Snapshot file cập nhật.
- Camera offline -> slot `Unknown`.
- Camera reconnect -> state phục hồi.

### 2.5 Burn-In

Chạy:

- 8 giờ nội bộ.
- 24 giờ trước nghiệm thu.

Theo dõi:

- Crash count.
- CPU/RAM.
- Camera reconnect count.
- Unknown slot count.
- WebSocket disconnect count.
- Disk log growth.

## 3. Acceptance Criteria

### Functional

- Mỗi slot enabled xuất hiện trong WebSocket payload.
- Payload có `timestamp`, `total_slots`, `slots`.
- Mỗi item có `camera_id`, `slot_id`, `state`.
- State chỉ là `Empty`, `Occupied`, `Unknown`.
- Tablet nhận state và update UI.
- Camera offline/stale làm slot thành `Unknown`.

### Performance

- 6 camera chạy đồng thời.
- CPU không giữ 100% liên tục trong điều kiện bình thường.
- RAM không tăng không kiểm soát.
- WebSocket push ổn định 2-5 Hz.
- State update đủ nhanh cho thao tác Tablet.

### Safety

- Không publish `Empty` khi camera stale/offline.
- Không flip `Empty` quá nhanh khi model miss ngắn hạn.
- `Unknown` không được coi là `Empty`.
- Vision không tự gửi task lên FMS.

## 4. Test Matrix

| Case | Input | Expected |
|---|---|---|
| Slot có hàng | Detection trong ROI ổn định | `Occupied` |
| Slot trống | Không detection qua exit window | `Empty` |
| Object ngoài ROI | Detection ngoài polygon | Không làm slot full |
| Camera offline | Không frame mới | `Unknown` |
| Inference stale | Không observation mới quá timeout | `Unknown` |
| Model miss ngắn | Mất detection 1-2 frame | Không flip Empty nếu chưa đủ exit |
| WebSocket reconnect | Tablet disconnect/connect lại | Nhận snapshot mới nhất |
| FMS rejected | Tablet gửi task, FMS lỗi | Tablet alert, Vision không liên quan |

## 5. Commissioning Checklist

- Chốt số camera.
- Chốt slot_id theo Tablet UI.
- Chụp ảnh reference từng camera.
- Vẽ ROI từng slot.
- Kiểm tra class model.
- Chạy replay.
- Chạy live từng camera.
- Chạy live đủ 6 camera.
- Test WebSocket với Tablet.
- Test Store vào slot `Empty`.
- Test Store vào slot `Occupied`.
- Test `Unknown`.
- Burn-in.

