import logging
from pathlib import Path
from datetime import datetime, timezone
import json

from app.celery_app import celery_app
from app.core.config import get_settings
from app.services.automl_service import prepare_job_paths

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.train_automl", track_started=True)
def train_automl(self, job_id: str) -> dict[str, str]:
    settings = get_settings()
    csv_path = Path(settings.upload_dir) / f"{job_id}.csv"
    started_at = datetime.now(timezone.utc)

    try:
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found for job {job_id}: {csv_path}")

        self.update_state(
            state="STARTED",
            meta={"job_id": job_id, "message": "Training started", "start_time": started_at.isoformat()},
        )

        paths = prepare_job_paths(settings, job_id)
        logger.info("Starting sample AutoML task for job %s", job_id)
        # --- Minimal artifact generation for API integration ---
        finished_at = datetime.now(timezone.utc)

        results = {
            "job_id": job_id,
            "best_model_name": "baseline-model",
            "best_model_score": 0.0,
            "evaluation_metric": "accuracy",
            "mlflow_run_id": None,
            "start_time": started_at.isoformat(),
            "end_time": finished_at.isoformat(),
        }

        results_file = Path(paths["artifacts"]) / "results.json"
        try:
            with results_file.open("w", encoding="utf-8") as fh:
                json.dump(results, fh, indent=2)
        except Exception:
            logger.exception("Failed to write results.json for job %s", job_id)

        logger.info("Completed sample AutoML task for job %s", job_id)
        return results
    except Exception as exc:
        logger.exception("AutoML task failed for job %s", job_id)
        self.update_state(
            state="FAILURE",
            meta={
                "job_id": job_id,
                "message": str(exc),
                "start_time": started_at.isoformat(),
                "end_time": datetime.now(timezone.utc).isoformat(),
            },
        )
        raise