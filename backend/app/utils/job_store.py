from __future__ import annotations

from datetime import datetime
from threading import Lock
from typing import Optional

from app.schemas.job import JobRecord


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = Lock()

    def create(self, job_id: str, profile: str = "balanced") -> JobRecord:
        with self._lock:
            record = JobRecord(job_id=job_id, profile=profile)
            self._jobs[job_id] = record
            return record

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

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
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
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
            self._jobs[job_id] = job
            return job
