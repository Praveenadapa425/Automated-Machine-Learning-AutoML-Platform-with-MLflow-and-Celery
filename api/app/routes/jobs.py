import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import get_settings
from app.schemas.job import JobCreateResponse, JobStatusResponse, JobResultsResponse
from app.services.job_status_service import build_job_status
from app.services.job_service import save_job_upload
from app.services.results_service import read_job_results

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobCreateResponse, status_code=202, summary="Create AutoML job")
async def create_job(
    csv_file: UploadFile = File(...),
    target_column: str = Form(...),
    task_type: str = Form(...),
    time_budget_seconds: int = Form(...),
) -> JobCreateResponse:
    settings = get_settings()
    result = await save_job_upload(
        settings=settings,
        upload_file=csv_file,
        target_column=target_column,
        task_type=task_type,
        time_budget_seconds=time_budget_seconds,
    )
    logger.info("Created job %s", result["job_id"])
    return JobCreateResponse(**result)


@router.get("/{job_id}", response_model=JobStatusResponse, summary="Get AutoML job status")
def get_job_status(job_id: str) -> JobStatusResponse:
    if not job_id.strip():
        raise HTTPException(status_code=404, detail="Job not found")
    return build_job_status(job_id)


@router.get("/{job_id}/results", response_model=JobResultsResponse, summary="Get AutoML job results")
def get_job_results(job_id: str) -> JobResultsResponse:
    if not job_id.strip():
        raise HTTPException(status_code=404, detail="Job not found")
    settings = get_settings()
    data = read_job_results(settings=settings, job_id=job_id)
    return JobResultsResponse(**data)