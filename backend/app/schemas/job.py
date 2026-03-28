from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    stage: str
    message: str
    download_url: Optional[str] = None
    profile: str
    engine_tier: Optional[str] = None
    failure_code: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    stage_timings: dict[str, float] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None


class JobRecord(BaseModel):
    job_id: str
    profile: str = "balanced"
    status: str = "queued"
    progress: int = 0
    stage: str = "queued"
    message: str = "Job accepted"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    output_glb_path: Optional[str] = None
    engine_tier: Optional[str] = None
    failure_code: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    stage_timings: dict[str, float] = Field(default_factory=dict)
    error: Optional[str] = None
