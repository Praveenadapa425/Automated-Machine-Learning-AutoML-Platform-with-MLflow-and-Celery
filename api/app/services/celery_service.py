import logging

from fastapi import HTTPException

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

try:
    from celery import Celery
    from celery.result import AsyncResult

    celery_app = Celery(
        "automl_api",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )

    celery_app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_track_started=True,
        enable_utc=True,
        timezone="UTC",
        broker_connection_retry_on_startup=True,
        worker_prefetch_multiplier=1,
    )
except ImportError:  # pragma: no cover - keeps the API bootable in lean dev shells.
    Celery = None
    AsyncResult = None
    celery_app = None


def enqueue_train_automl(job_id: str) -> None:
    if celery_app is None:
        raise HTTPException(status_code=503, detail="Celery dependencies are not installed")
    logger.info("Enqueuing train_automl task for job %s", job_id)
    celery_app.send_task(
        "app.tasks.train_automl",
        args=[job_id],
        task_id=job_id,
        queue="automl",
    )


def get_job_task_result(job_id: str) -> AsyncResult:
    if celery_app is None or AsyncResult is None:
        raise HTTPException(status_code=503, detail="Celery dependencies are not installed")
    return AsyncResult(job_id, app=celery_app)