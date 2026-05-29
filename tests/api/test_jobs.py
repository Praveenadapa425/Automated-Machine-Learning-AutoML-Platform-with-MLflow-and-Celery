import os
from pathlib import Path

import importlib.util
import sys

import pytest


def _prep_api_path():
    repo_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "api" / "app" / "main.py").exists()
    )
    api_path = repo_root / "api"
    # Ensure api is first on sys.path
    if str(api_path) not in sys.path:
        sys.path.insert(0, str(api_path))


@pytest.fixture
def client(monkeypatch, tmp_path):
    _prep_api_path()
    # Import app.main directly from the api package path to avoid worker/api name clashes.
    repo_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "api" / "app" / "main.py").exists()
    )
    app_main_path = repo_root / "api" / "app" / "main.py"
    spec = importlib.util.spec_from_file_location("api_app_main", app_main_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    app = module.app

    # Monkeypatch celery enqueue to avoid requiring Celery in test env
    import app.services.celery_service as celery_service
    import app.services.job_service as job_service
    import app.services.job_status_service as job_status_service
    monkeypatch.setattr(celery_service, "enqueue_train_automl", lambda job_id: None)
    monkeypatch.setattr(job_service, "enqueue_train_automl", lambda job_id: None)

    # Fake task result for status endpoint
    from types import SimpleNamespace

    def fake_get_job_task_result(job_id: str):
        return SimpleNamespace(state="PENDING", info=None, result=None)

    monkeypatch.setattr(job_status_service, "get_job_task_result", fake_get_job_task_result)

    from fastapi.testclient import TestClient

    yield TestClient(app)


def test_create_job_and_status_and_results(client, tmp_path):
    # small CSV
    csv_content = "a,b,target\n1,2,0\n3,4,1\n"
    files = {"csv_file": ("sample.csv", csv_content, "text/csv")}
    data = {
        "target_column": "target",
        "task_type": "classification",
        "time_budget_seconds": "30",
    }
    r = client.post("/jobs", files=files, data=data)
    assert r.status_code == 202
    body = r.json()
    assert "job_id" in body
    job_id = body["job_id"]

    # upload file and meta exist
    upload_dir = Path(os.environ.get("UPLOAD_DIR"))
    assert (upload_dir / f"{job_id}.csv").exists()
    assert (upload_dir / f"{job_id}.meta.json").exists()

    # status endpoint
    s = client.get(f"/jobs/{job_id}")
    assert s.status_code == 200
    js = s.json()
    assert js["status"] == "PENDING"

    # results not present yet
    r2 = client.get(f"/jobs/{job_id}/results")
    assert r2.status_code == 404
