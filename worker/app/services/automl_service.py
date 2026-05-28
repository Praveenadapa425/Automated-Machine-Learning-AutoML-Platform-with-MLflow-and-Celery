from pathlib import Path

from app.core.config import Settings
from app.services.artifact_service import build_job_directory, build_report_directory


def prepare_job_paths(settings: Settings, job_id: str) -> dict[str, Path]:
    return {
        "artifacts": build_job_directory(settings, job_id),
        "reports": build_report_directory(settings, job_id),
    }