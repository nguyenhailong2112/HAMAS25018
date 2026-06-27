# Project Spec

## 1. Mục Tiêu

HAMAS25018 là hệ thống Vision Server dùng camera CCTV để giám sát trạng thái các slot/vị trí chứa hàng. Hệ thống đóng vai trò cảm biến thông minh trước khi người vận hành thao tác gọi nhiệm vụ trên Tablet/Caller App.

Mục tiêu chính:

- Chạy liên tục 24/7.
- Quan sát các slot đã được cấu hình.
- Kết luận slot đang `Empty`, `Occupied` hoặc `Unknown`.
- Push trạng thái slot liên tục cho Tablet bằng WebSocket.
- Tablet dùng trạng thái này để validate trước khi gửi lệnh task lên FMS.

## 2. Phần Cứng Mục Tiêu

- CPU: Intel Core i5-14500.
- RAM: 8GB.
- GPU: không sử dụng trong production runtime.
- Camera: 6 luồng CCTV.
- Runtime: CPU-only.

## 3. Vai Trò Của Vision Server

Vision Server là **Occupancy Sensor Server**.

Vision trả lời câu hỏi duy nhất:

```text
Slot này hiện tại có hàng, không có hàng, hay không xác định?
```

Vision không trả lời:

- Có nên tạo task hay không.
- Có nên điều phối AGV/FMR hay không.
- FMS nên chọn robot nào.
- Mission nào được ưu tiên.
- User có được phép override cảnh báo hay không.

Các quyết định đó thuộc về Tablet/Caller App và FMS.

## 4. Process Nghiệp Vụ Chính

### Phase 1: Monitoring

Vision quan sát camera liên tục:

```text
Camera
  -> AI Detection
  -> Slot Occupancy State
  -> WebSocket
  -> Tablet / Caller App
```

Tablet nhận trạng thái và update UI real-time.

### Phase 2: Validation

User thao tác trên Tablet:

- Pick.
- Store.
- Cycle.
- Task type khác nếu sau này có.

Trước khi gửi lệnh lên FMS, Tablet tự kiểm tra slot đích/slot liên quan.

Ví dụ Store mission:

```text
Slot đích phải là Empty.
```

Nếu slot là `Occupied` hoặc `Unknown`, Tablet hiển thị warning modal. User có thể `Continue` hoặc `Cancel` tùy rule vận hành đã thống nhất.

### Phase 3: Dispatch

Sau khi user xác nhận, Tablet gửi task lên FMS:

```http
POST /sendTask
```

Ví dụ:

```json
{
  "type": "Store",
  "nodePick": "A01",
  "nodeStore": "B03"
}
```

FMS trả:

- Success: task accepted.
- Failure: task rejected, Tablet alert user.

## 5. State Public

### `Empty`

Vision không thấy hàng trong slot sau khi qua logic ổn định.

Ý nghĩa với Tablet:

- Store vào slot có thể hợp lệ.
- Các rule cụ thể vẫn do Tablet/FMS quyết định.

### `Occupied`

Vision thấy slot đang có hàng.

Ý nghĩa với Tablet:

- Nếu user muốn Store vào slot này, phải cảnh báo.
- Nếu mission là Pick từ slot này, trạng thái này có thể là điều kiện hợp lệ tùy business rule của Tablet.

### `Unknown`

Vision không đủ chắc chắn.

Nguyên nhân:

- Camera offline.
- Frame stale.
- Model chưa ổn định.
- Runtime warm-up.
- Slot bị che khuất.
- Config/ROI lỗi.

Ý nghĩa với Tablet:

- Không được xem là `Empty`.
- Nên cảnh báo hoặc yêu cầu user xác nhận.

## 6. Scope In

Hạng mục thuộc phạm vi Vision:

- Đọc 6 camera CCTV.
- CPU-only inference.
- ROI theo slot.
- Detect object trong slot.
- Hysteresis chống flicker.
- Unknown timeout.
- In-memory slot state store.
- WebSocket broadcast cho Tablet.
- REST endpoint tối giản để debug/fallback.
- JSON snapshot tối giản.
- Preview/debug frame phục vụ kỹ thuật nếu cần.
- Log vận hành và state change.
- Watchdog/service chạy 24/7.

## 7. Scope Out

Không triển khai trong main process:

- Elevator process.
- HIK outbound bridge.
- Gọi API FMS.
- Gọi API server điều phối tổng.
- Tạo task.
- Business validation trong Vision.
- WMS/WCS logic.
- Mapping pallet/trolley phức tạp nếu Tablet chưa cần.
- `storageBinCode`, `ctnr_typ`, HIK mapping trong payload chính.

Các field/mapping mở rộng có thể giữ ở config nội bộ nếu sau này cần, nhưng không được làm phức tạp phase triển khai chính.

## 8. Definition Of Done

Hệ thống đạt yêu cầu khi:

- Vision Server chạy ổn định với camera thật hoặc source test.
- Mỗi slot có state mới nhất.
- WebSocket push payload đúng contract.
- Tablet có thể nhận state và update UI.
- Camera offline/stale làm slot thành `Unknown`.
- Không còn dependency runtime vào elevator/HIK/FMS.
- Có REST health và slot snapshot tối giản.
- Có log đủ để debug vận hành.
- Có tài liệu test và deployment rõ ràng.

