from __future__ import annotations

import json
import time
from pathlib import Path

import cv2


def _temp_path_for(path: Path) -> Path:
    return path.with_name(f".{path.name}.tmp")


def write_text_atomic(path: Path, text: str, *, encoding: str = "utf-8") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _temp_path_for(path)
    tmp_path.write_text(text, encoding=encoding)
    tmp_path.replace(path)
    return path


def write_json_atomic(path: Path, payload, *, encoding: str = "utf-8", indent: int | None = 2) -> Path:
    separators = None if indent is not None else (",", ":")
    return write_text_atomic(
        path,
        json.dumps(payload, ensure_ascii=False, indent=indent, separators=separators),
        encoding=encoding,
    )


def write_image_atomic(path: Path, frame, *, quality: int = 92) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _temp_path_for(path)
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    elif suffix == ".png":
        ok, encoded = cv2.imencode(".png", frame)
    else:
        raise ValueError(f"Unsupported image suffix for atomic write: {path.suffix}")
    if not ok:
        raise ValueError(f"Failed to encode image for {path}")
    tmp_path.write_bytes(encoded.tobytes())
    tmp_path.replace(path)
    return path


def rotate_backups(path: Path, backup_count: int) -> None:
    if backup_count <= 0:
        if path.exists():
            path.unlink()
        return
    oldest = path.with_name(f"{path.name}.{backup_count}")
    if oldest.exists():
        oldest.unlink()
    for index in range(backup_count - 1, 0, -1):
        src = path.with_name(f"{path.name}.{index}")
        dst = path.with_name(f"{path.name}.{index + 1}")
        if src.exists():
            src.replace(dst)
    if path.exists():
        path.replace(path.with_name(f"{path.name}.1"))


def append_jsonl_rotating(
    path: Path,
    payload: dict,
    *,
    max_bytes: int = 20 * 1024 * 1024,
    backup_count: int = 5,
    encoding: str = "utf-8",
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and max_bytes > 0 and path.stat().st_size >= max_bytes:
        rotate_backups(path, backup_count)
    with path.open("a", encoding=encoding) as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return path


def tail_text_lines(path: Path, limit: int = 100, encoding: str = "utf-8") -> list[str]:
    if limit <= 0 or not path.exists():
        return []
    with path.open("r", encoding=encoding, errors="replace") as f:
        lines = f.readlines()
    return [line.rstrip("\n") for line in lines[-limit:]]


def purge_older_than(root: Path, *, max_age_sec: float, now_ts: float | None = None) -> int:
    if max_age_sec <= 0 or not root.exists():
        return 0
    now = time.time() if now_ts is None else float(now_ts)
    cutoff = now - max_age_sec
    removed = 0
    for path in root.rglob("*"):
        try:
            if not path.is_file():
                continue
            if path.stat().st_mtime >= cutoff:
                continue
            path.unlink()
            removed += 1
        except FileNotFoundError:
            continue
        except OSError:
            continue
    return removed
