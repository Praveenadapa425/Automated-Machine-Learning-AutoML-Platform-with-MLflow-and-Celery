import logging

from fastapi import APIRouter, File, Form, UploadFile

from app.core.config import get_settings
from app.schemas.job import JobCreateResponse
from app.services.job_service import save_job_upload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobCreateResponse, status_code=201, summary="Create AutoML job")
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