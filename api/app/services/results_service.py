import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.core.config import Settings


def read_job_results(settings: Settings, job_id: str) -> dict[str, Any]:
    artifacts_root = Path(settings.artifacts_dir)
    results_file = artifacts_root / job_id / "results.json"
    if not results_file.exists():
        raise HTTPException(status_code=404, detail="Results not found for job")

    try:
        with results_file.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to read results file") from exc

    # Ensure job_id present
    data.setdefault("job_id", job_id)
    return data
