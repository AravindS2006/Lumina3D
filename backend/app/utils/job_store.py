from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Optional

from app.schemas.job import JobRecord


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def create(self, job_id: str) -> JobRecord:
        with self._lock:
            record = JobRecord(job_id=job_id)
            self._jobs[job_id] = record
            return record

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        stage: Optional[str] = None,
        message: Optional[str] = None,
        output_glb_path: Optional[str] = None,
        error: Optional[str] = None,
    ) -> Optional[JobRecord]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
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
            if error is not None:
                job.error = error
            job.updated_at = datetime.utcnow()
            self._jobs[job_id] = job
            return job
