from pathlib import Path
from uuid import UUID

from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.job import JobStatusResponse
from app.services.celery_service import get_job_task_result


def _map_state_to_status(celery_state: str) -> str:
    mapping = {
        "PENDING": "PENDING",
        "STARTED": "RUNNING",
        "SUCCESS": "SUCCESS",
        "FAILURE": "FAILED",
    }
    return mapping.get(celery_state, celery_state)


def build_job_status(job_id: str) -> JobStatusResponse:
    try:
        UUID(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc

    upload_path = Path(get_settings().upload_dir) / f"{job_id}.csv"
    if not upload_path.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    task_result = get_job_task_result(job_id)
    celery_state = task_result.state
    start_time = None
    end_time = None

    if task_result.info and isinstance(task_result.info, dict):
        start_time = task_result.info.get("start_time")
        end_time = task_result.info.get("end_time")

    if celery_state == "SUCCESS" and isinstance(task_result.result, dict):
        start_time = task_result.result.get("start_time", start_time)
        end_time = task_result.result.get("end_time", end_time)
    elif celery_state == "FAILURE" and isinstance(task_result.result, dict):
        start_time = task_result.result.get("start_time", start_time)
        end_time = task_result.result.get("end_time", end_time)
    elif celery_state == "PENDING":
        end_time = None

    if end_time is None and getattr(task_result, "date_done", None) is not None:
        end_time = task_result.date_done.isoformat()

    return JobStatusResponse(
        job_id=job_id,
        status=_map_state_to_status(celery_state),
        start_time=start_time,
        end_time=end_time,
    )