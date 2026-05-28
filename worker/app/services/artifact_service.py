from pathlib import Path

from app.core.config import Settings


def build_job_directory(settings: Settings, job_id: str) -> Path:
    job_dir = Path(settings.artifacts_dir) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def build_report_directory(settings: Settings, job_id: str) -> Path:
    report_dir = Path(settings.reports_dir) / job_id
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir