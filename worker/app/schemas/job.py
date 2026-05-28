from enum import Enum

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    started = "started"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobArtifact(BaseModel):
    name: str = Field(..., examples=["leaderboard.csv"])
    path: str = Field(..., examples=["/data/artifacts/job-123/leaderboard.csv"])


class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    message: str
    artifacts: list[JobArtifact] = []