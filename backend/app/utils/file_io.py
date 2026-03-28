from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
UPLOADS_DIR = ROOT / "uploads"
OUTPUTS_DIR = ROOT / "outputs"
TMP_DIR = ROOT / "tmp"


def ensure_dirs() -> None:
    for directory in (UPLOADS_DIR, OUTPUTS_DIR, TMP_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def job_dir(job_id: str) -> Path:
    directory = OUTPUTS_DIR / job_id
    directory.mkdir(parents=True, exist_ok=True)
    return directory
