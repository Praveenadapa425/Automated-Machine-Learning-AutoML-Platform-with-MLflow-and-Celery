from pydantic import BaseModel, Field


class JobCreateResponse(BaseModel):
    job_id: str = Field(..., description="Generated job identifier")
    status: str = Field(default="PENDING")