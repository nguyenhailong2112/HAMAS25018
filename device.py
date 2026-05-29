import torch
import os

from core.inference_runtime import YOLO_DEVICE

print(torch.__version__)
print(torch.version.cuda)
print("YOLO_DEVICE:", YOLO_DEVICE)
print("CUDA_VISIBLE_DEVICES:", os.environ.get("CUDA_VISIBLE_DEVICES"))
print("CUDA:", torch.cuda.is_available())
print(torch.cuda.device_count())
if torch.cuda.is_available():
    print("DEVICE:", torch.cuda.get_device_name(0))
else:
    print("DEVICE: CPU-only runtime")