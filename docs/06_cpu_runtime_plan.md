# CPU Runtime Plan

## 1. Mục Tiêu

Chạy 6 camera trên PC i5-14500/8GB RAM, CPU-only, ổn định 24/7.

Với bài toán slot occupancy, ưu tiên:

- State đúng và ổn định.
- Latency đủ thấp cho Tablet.
- Không backlog frame.
- Không quá tải CPU/RAM.

Không cần inference 25 FPS/camera.

## 2. Target Runtime

Đề xuất ban đầu:

- Decode: 5-8 FPS/camera.
- Inference: 1-3 FPS/camera.
- WebSocket push: 2-5 Hz.
- REST health: on-demand.
- Preview/debug: 1-2 FPS nếu bật.

## 3. Camera Strategy

Ưu tiên:

- `latest_frame_only = true`.
- RTSP TCP.
- Buffer size thấp.
- Sub-stream nếu đủ rõ.

Nếu sub-stream làm model miss nhiều, dùng main-stream nhưng giảm infer FPS.

## 4. Inference Scheduler

Scheduler nên đơn giản:

```text
Round-robin theo camera, chọn frame mới nhất, bỏ frame cũ.
```

Rule:

- Không infer lại cùng `frame_id`.
- Camera offline thì không infer.
- Camera overdue hơn được ưu tiên.
- Không tạo queue dài.

Batch:

- `batch_size = 1` mặc định cho CPU.
- Chỉ thử batch > 1 khi benchmark thực tế chứng minh tốt hơn.

## 5. Model Settings

Đề xuất:

```json
{
  "conf_threshold": 0.5,
  "img_size": 416
}
```

Nếu CPU cao:

1. Giảm debug/preview FPS.
2. Giảm inference FPS.
3. Giảm image size xuống 320.
4. Chuyển sub-stream.
5. Dùng model nhỏ hơn.

## 6. State Timing

Đề xuất:

```json
{
  "enter_window": 3,
  "enter_count": 2,
  "exit_window": 7,
  "exit_count": 5,
  "unknown_timeout_sec": 3.0
}
```

Mapping:

- Object xuất hiện ổn định -> `Occupied`.
- Object vắng mặt ổn định -> `Empty`.
- Không cập nhật đủ mới -> `Unknown`.

Lý do:

- False Empty nguy hiểm hơn False Full.
- Khi model miss ngắn hạn, không được flip sang `Empty` quá nhanh.
- Camera stale không được giữ state cũ mãi.

## 7. RAM Budget

Runtime chỉ nên giữ:

- Latest frame mỗi camera.
- Last detection result mỗi camera.
- Slot state store.
- Model cache.
- Preview/debug frame resized nếu cần.

Không giữ:

- Frame queue dài.
- Video recording mặc định.
- Debug image full-res liên tục.

## 8. WebSocket Load

Payload nhỏ, có thể push full snapshot 2-5 Hz.

Nếu nhiều Tablet connect:

- Broadcast cùng một snapshot.
- Không build payload riêng phức tạp cho từng client.
- Không trigger inference theo client request.

## 9. Benchmark Cần Có

Trước nghiệm thu:

- CPU average/peak.
- RAM sau 1h/8h/24h.
- Inference ms/frame.
- Effective infer FPS/camera.
- WebSocket push ổn định.
- Camera reconnect behavior.
- Tỷ lệ `Unknown`.
- False Empty/False Full trên video test.

## 10. Nguyên Tắc Tối Ưu

Không tối ưu sớm bằng cách làm phức tạp kiến trúc.

Thứ tự đúng:

1. Chạy đúng.
2. Chạy ổn định.
3. Đo CPU/RAM.
4. Tune FPS/img_size/model.
5. Chỉ thêm tối ưu runtime sâu nếu thật sự cần.

