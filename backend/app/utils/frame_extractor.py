from __future__ import annotations

from pathlib import Path

import cv2


FRAME_LABELS = ["front", "right", "back", "left"]


def extract_keyframes(video_path: Path, output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError(f"Unable to open video: {video_path}")

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if frame_count <= 0:
        capture.release()
        raise ValueError("Video has no frames")

    indices = [int(frame_count * i / 4) for i in range(4)]
    saved: list[Path] = []

    for label, idx in zip(FRAME_LABELS, indices):
        capture.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = capture.read()
        if not ok:
            continue
        file_path = output_dir / f"{label}.png"
        cv2.imwrite(str(file_path), frame)
        saved.append(file_path)

    capture.release()
    if len(saved) != 4:
        raise ValueError("Failed to extract all four keyframes")
    return saved
