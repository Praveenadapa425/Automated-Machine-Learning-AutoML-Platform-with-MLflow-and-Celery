from pydantic import BaseModel, Field


class JobCreateResponse(BaseModel):
    job_id: str = Field(..., description="Generated job identifier")
    status: str = Field(default="PENDING")


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    start_time: str | None = None
    end_time: str | None = None


class JobResultsResponse(BaseModel):
    job_id: str
    best_model_name: str | None = None
    best_model_score: float | None = None
    evaluation_metric: str | None = None
    mlflow_run_id: str | None = None