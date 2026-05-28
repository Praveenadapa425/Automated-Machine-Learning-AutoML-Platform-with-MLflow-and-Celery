import logging
from pathlib import Path

from app.celery_app import celery_app
from app.core.config import get_settings
from app.services.automl_service import prepare_job_paths

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.jobs.process_job")
def process_job(job_id: str, csv_path: str) -> dict[str, str]:
    settings = get_settings()
    source_file = Path(csv_path)

    if not source_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    paths = prepare_job_paths(settings, job_id)
    logger.info("Prepared directories for job %s at %s", job_id, paths["artifacts"])

    return {
        "job_id": job_id,
        "status": "queued",
        "csv_path": str(source_file),
        "artifacts_dir": str(paths["artifacts"]),
        "reports_dir": str(paths["reports"]),
    }