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
    created_at: datetime
    updated_at: datetime
    error: Optional[str] = None


class JobRecord(BaseModel):
    job_id: str
    status: str = "queued"
    progress: int = 0
    stage: str = "queued"
    message: str = "Job accepted"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    output_glb_path: Optional[str] = None
    error: Optional[str] = None
