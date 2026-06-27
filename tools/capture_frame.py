import sys
from pathlib import Path
import cv2
import re

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parent.parent

VIDEO_ROOT = PROJECT_ROOT / "VideoRaw"
IMAGE_ROOT = PROJECT_ROOT / "ImageRaw"

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

IP_PATTERN = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")

def find_ip_from_path(path: Path) -> str:
    for part in path.parts:
        match = IP_PATTERN.search(part)
        if match:
            return match.group()

    return "Unknown"


def extract_frames(video_path: Path):
    ip = find_ip_from_path(video_path)

    output_dir = IMAGE_ROOT / ip
    output_dir.mkdir(parents=True, exist_ok=True)

    video_name = video_path.stem

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        print(f"[ERROR] Cannot open: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 25

    frame_interval = int(round(fps))

    frame_idx = 0
    save_idx = 0

    print(f"\nProcessing: {video_path}")
    print(f"IP        : {ip}")
    print(f"FPS       : {fps:.2f}")

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        if frame_idx % frame_interval == 0:

            image_name = (
                f"{video_name}_{save_idx:06d}.jpg"
            )

            save_path = output_dir / image_name

            cv2.imwrite(
                str(save_path),
                frame
            )

            save_idx += 1

        frame_idx += 1

    cap.release()

    print(
        f"Saved {save_idx} images"
    )

def main():

    if not VIDEO_ROOT.exists():
        print(
            f"Video folder not found:\n{VIDEO_ROOT}"
        )
        return

    video_files = []

    for ext in VIDEO_EXTENSIONS:
        video_files.extend(
            VIDEO_ROOT.rglob(f"*{ext}")
        )

    video_files = sorted(video_files)

    print(f"Found {len(video_files)} video(s)")

    for video_file in video_files:
        extract_frames(video_file)

    print("\nDONE")

if __name__ == "__main__":
    main()
