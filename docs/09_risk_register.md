# Risk Register

## 1. False Empty

Mô tả: Vision báo `Empty` trong khi thực tế slot có hàng.

Tác động: Tablet có thể cho phép user gửi Store task vào slot đã có hàng nếu user không kiểm tra hiện trường.

Giảm thiểu:

- Exit hysteresis chặt hơn enter.
- Camera stale/offline phải thành `Unknown`.
- ROI đủ phủ vùng hàng.
- Ưu tiên recall model.
- Test thực tế từng slot.

## 2. False Full

Mô tả: Vision báo `Occupied` trong khi slot trống.

Tác động: Tablet cảnh báo không cần thiết, giảm hiệu suất.

Giảm thiểu:

- Tune confidence threshold.
- ROI tránh vùng nhiễu.
- Debug frame khi commissioning.
- Test object gây nhiễu.

## 3. Unknown Quá Nhiều

Mô tả: nhiều slot thường xuyên `Unknown`.

Tác động: Tablet cảnh báo nhiều, vận hành bị chậm.

Nguyên nhân:

- Camera mất kết nối.
- Infer FPS quá thấp so với timeout.
- Model không ổn.
- ROI sai.

Giảm thiểu:

- Tune `unknown_timeout_sec`.
- Theo dõi camera health.
- Tăng infer FPS nếu CPU cho phép.
- Chỉnh ROI/model.

## 4. WebSocket Disconnect

Mô tả: Tablet mất kết nối Vision.

Tác động: Tablet không có state mới.

Giảm thiểu:

- Tablet auto reconnect.
- Vision push full snapshot sau reconnect.
- Health endpoint để kiểm tra.
- Network ổn định nội bộ.

## 5. CPU Overload

Mô tả: PC xử lý không kịp 6 camera.

Tác động:

- State update chậm.
- Unknown tăng.
- WebSocket vẫn sống nhưng state stale.

Giảm thiểu:

- Latest frame only.
- Infer FPS hợp lý.
- Batch size 1.
- Sub-stream.
- Giảm debug/preview.
- Dùng model nhỏ hơn.

## 6. ROI Sai

Mô tả: slot_id đúng nhưng polygon sai.

Tác động:

- Slot state sai.
- Tablet UI sai.

Giảm thiểu:

- Ảnh reference từng camera.
- Debug overlay label slot.
- Review ROI với team hiện trường.
- Test từng slot.

## 7. Slot ID Không Khớp Tablet

Mô tả: Vision gửi `slot_id` khác mapping UI Tablet.

Tác động: Tablet cảnh báo/suy luận sai slot.

Giảm thiểu:

- Chốt bảng mapping camera_id/slot_id với Tablet team.
- Test từng slot trên UI.
- Không đổi slot_id production tùy tiện.

## 8. Vision Bị Gán Sai Trách Nhiệm

Mô tả: hệ thống ngoài kỳ vọng Vision tạo task hoặc quyết định business rule.

Tác động: scope phình to, khó vận hành.

Giảm thiểu:

- Contract ghi rõ Vision là occupancy sensor.
- Tablet là business validation layer.
- FMS là execution layer.

## 9. Camera Lệch Góc Sau Thời Gian

Mô tả: camera bị rung/lệch làm ROI không còn đúng.

Tác động: state sai hàng loạt.

Giảm thiểu:

- Cố định camera chắc.
- Có ảnh reference.
- Có quy trình recalibrate ROI.
- Debug preview định kỳ.

## 10. User Override Warning

Mô tả: Tablet cho user Continue dù slot không hợp lệ.

Tác động: rủi ro vận hành thực địa.

Phạm vi xử lý:

- Đây là business rule của Tablet/team vận hành.
- Vision chỉ cung cấp state đúng nhất có thể.

Giảm thiểu phía Vision:

- State rõ ràng.
- Unknown không mập mờ.
- Timestamp mới.

