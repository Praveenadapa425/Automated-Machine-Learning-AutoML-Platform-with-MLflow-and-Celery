import csv
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from app.core.config import Settings
from app.services.celery_service import enqueue_train_automl
import json

logger = logging.getLogger(__name__)


def _validate_task_type(task_type: str) -> str:
    normalized_task_type = task_type.strip().lower()
    if normalized_task_type not in {"classification", "regression"}:
        raise HTTPException(status_code=400, detail="task_type must be classification or regression")
    return normalized_task_type


def _validate_csv_file(upload_file: UploadFile) -> None:
    filename = upload_file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content_type = (upload_file.content_type or "").lower()
    allowed_types = {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"}
    if content_type and content_type not in allowed_types:
        logger.warning("Unexpected upload content type: %s", content_type)


async def save_job_upload(
    settings: Settings,
    upload_file: UploadFile,
    target_column: str,
    task_type: str,
    time_budget_seconds: int,
) -> dict[str, str]:
    validated_task_type = _validate_task_type(task_type)
    _validate_csv_file(upload_file)

    if not target_column.strip():
        raise HTTPException(status_code=400, detail="target_column is required")
    if time_budget_seconds <= 0:
        raise HTTPException(status_code=400, detail="time_budget_seconds must be greater than zero")

    job_id = str(uuid4())
    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    file_path = upload_root / f"{job_id}.csv"

    try:
        contents = await upload_file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="CSV file is empty")

        decoded = contents.decode("utf-8-sig")
        sample = decoded.splitlines()[:2]
        if not sample:
            raise HTTPException(status_code=400, detail="CSV file is missing a header row")

        csv.Sniffer().sniff("\n".join(sample))

        file_path.write_text(decoded, encoding="utf-8")

        # persist job metadata for the worker
        metadata = {
            "job_id": job_id,
            "target_column": target_column,
            "task_type": validated_task_type,
            "time_budget_seconds": int(time_budget_seconds),
        }
        meta_path = upload_root / f"{job_id}.meta.json"
        meta_path.write_text(json.dumps(metadata), encoding="utf-8")

        enqueue_train_automl(job_id)

        logger.info(
            "Saved job upload %s to %s and queued task for task_type=%s target_column=%s time_budget_seconds=%s",
            job_id,
            file_path,
            validated_task_type,
            target_column,
            time_budget_seconds,
        )
        return {"job_id": job_id, "status": "PENDING"}
    except HTTPException:
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        raise
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded") from exc
    except csv.Error as exc:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid CSV") from exc
    except Exception as exc:
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        logger.exception("Failed to queue AutoML job %s", job_id)
        raise HTTPException(status_code=503, detail="Failed to queue AutoML job") from exc
    finally:
        await upload_file.close()