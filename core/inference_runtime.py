from __future__ import annotations

import os

YOLO_DEVICE = "cpu"
CPU_ONLY_CUDA_VISIBLE_DEVICES = "-1"


def force_cpu_only_runtime() -> None:
    os.environ["CUDA_VISIBLE_DEVICES"] = CPU_ONLY_CUDA_VISIBLE_DEVICES

force_cpu_only_runtime()