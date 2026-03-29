from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.schemas.job import JobRecord

_DB_PATH = Path(
    os.getenv(
        "LUMINA_JOB_DB",
        str(Path(__file__).resolve().parents[2] / "outputs" / "jobs.db"),
    )
)


def _open() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        data   TEXT NOT NULL,
        updated_at TEXT NOT NULL
        )"""
    )
    conn.commit()
    return conn


class JobStore:
    def create(self, job_id: str, profile: str = "balanced") -> JobRecord:
        record = JobRecord(job_id=job_id, profile=profile)
        now = datetime.utcnow().isoformat()
        conn = _open()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO jobs (job_id, data, updated_at) VALUES (?, ?, ?)",
                (job_id, record.model_dump_json(), now),
            )
            conn.commit()
        finally:
            conn.close()
        return record

    def get(self, job_id: str) -> Optional[JobRecord]:
        conn = _open()
        try:
            row = conn.execute(
                "SELECT data FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        finally:
            conn.close()
        if not row:
            return None
        return JobRecord.model_validate_json(row[0])

    def update(
        self,
        job_id: str,
        *,
        profile: Optional[str] = None,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        stage: Optional[str] = None,
        message: Optional[str] = None,
        output_glb_path: Optional[str] = None,
        engine_tier: Optional[str] = None,
        failure_code: Optional[str] = None,
        warnings: Optional[list[str]] = None,
        stage_timings: Optional[dict[str, float]] = None,
        error: Optional[str] = None,
    ) -> Optional[JobRecord]:
        conn = _open()
        try:
            row = conn.execute(
                "SELECT data FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
            if not row:
                return None

            job = JobRecord.model_validate_json(row[0])
            if profile is not None:
                job.profile = profile
            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = progress
            if stage is not None:
                job.stage = stage
            if message is not None:
                job.message = message
            if output_glb_path is not None:
                job.output_glb_path = output_glb_path
            if engine_tier is not None:
                job.engine_tier = engine_tier
            if failure_code is not None:
                job.failure_code = failure_code
            if warnings is not None:
                job.warnings = warnings
            if stage_timings is not None:
                job.stage_timings = stage_timings
            if error is not None:
                job.error = error
            job.updated_at = datetime.utcnow()

            now = datetime.utcnow().isoformat()
            conn.execute(
                "UPDATE jobs SET data = ?, updated_at = ? WHERE job_id = ?",
                (job.model_dump_json(), now, job_id),
            )
            conn.commit()
        finally:
            conn.close()
        return job
