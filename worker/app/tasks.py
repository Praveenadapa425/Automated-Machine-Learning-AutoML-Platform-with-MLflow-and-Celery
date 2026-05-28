import logging
from pathlib import Path

from app.celery_app import celery_app
from app.core.config import get_settings
from app.services.automl_service import prepare_job_paths

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.train_automl", track_started=True)
def train_automl(self, job_id: str) -> dict[str, str]:
    settings = get_settings()
    csv_path = Path(settings.upload_dir) / f"{job_id}.csv"

    try:
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found for job {job_id}: {csv_path}")

        self.update_state(state="STARTED", meta={"job_id": job_id, "message": "Training started"})

        paths = prepare_job_paths(settings, job_id)
        logger.info("Starting sample AutoML task for job %s", job_id)

        result = {
            "job_id": job_id,
            "message": "Sample AutoML task completed",
            "artifacts_dir": str(paths["artifacts"]),
            "reports_dir": str(paths["reports"]),
            "csv_path": str(csv_path),
        }

        logger.info("Completed sample AutoML task for job %s", job_id)
        return result
    except Exception as exc:
        logger.exception("AutoML task failed for job %s", job_id)
        self.update_state(state="FAILURE", meta={"job_id": job_id, "message": str(exc)})
        raise