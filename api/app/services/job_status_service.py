from app.schemas.job import JobStatusResponse
from app.services.celery_service import get_job_task_result


def _map_state_to_status(celery_state: str) -> str:
    mapping = {
        "PENDING": "PENDING",
        "STARTED": "RUNNING",
        "SUCCESS": "COMPLETED",
        "FAILURE": "FAILED",
        "RETRY": "RETRYING",
        "REVOKED": "REVOKED",
    }
    return mapping.get(celery_state, celery_state)


def build_job_status(job_id: str) -> JobStatusResponse:
    task_result = get_job_task_result(job_id)
    celery_state = task_result.state
    detail = None

    if task_result.info and isinstance(task_result.info, dict):
        detail = task_result.info.get("message") or task_result.info.get("detail")
    elif task_result.info is not None:
        detail = str(task_result.info)

    return JobStatusResponse(
        job_id=job_id,
        status=_map_state_to_status(celery_state),
        celery_state=celery_state,
        detail=detail,
    )