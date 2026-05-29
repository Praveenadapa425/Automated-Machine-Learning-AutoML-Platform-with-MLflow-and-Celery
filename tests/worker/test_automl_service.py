import sys
from pathlib import Path

from types import SimpleNamespace

import os
import pytest
import types


def _prep_worker_path():
    repo_root = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "worker" / "app" / "services" / "automl_service.py").exists()
    )
    worker_root = repo_root / "worker"
    # Remove any existing 'app' modules to avoid cross-package conflicts
    for key in list(sys.modules.keys()):
        if key == "app" or key.startswith("app."):
            del sys.modules[key]
    if str(worker_root) not in sys.path:
        sys.path.insert(0, str(worker_root))


def test_run_full_automl_creates_artifacts(monkeypatch, tmp_path):
    _prep_worker_path()

    # Provide light-weight stubs for optional heavy dependencies before importing the module.
    fake_mlflow = types.ModuleType("mlflow")
    fake_mlflow.set_tracking_uri = lambda uri: None
    fake_mlflow.set_experiment = lambda name: None

    class _FakeRunCtx:
        def __enter__(self):
            return SimpleNamespace(info=SimpleNamespace(run_id="fake-run-id"))

        def __exit__(self, exc_type, exc, tb):
            return False

    fake_mlflow.start_run = lambda: _FakeRunCtx()
    fake_mlflow.log_param = lambda *args, **kwargs: None
    fake_mlflow.log_metric = lambda *args, **kwargs: None
    fake_mlflow.log_artifact = lambda *args, **kwargs: None

    fake_flaml = types.ModuleType("flaml")

    class FakeAutoML:
        def __init__(self):
            self.model = SimpleNamespace()

        def fit(self, X, y, **kwargs):
            return self

        def predict(self, X):
            try:
                return [0] * len(X)
            except Exception:
                return []

    fake_flaml.AutoML = FakeAutoML

    monkeypatch.setitem(sys.modules, "mlflow", fake_mlflow)
    monkeypatch.setitem(sys.modules, "flaml", fake_flaml)

    # set env dirs
    os.environ["UPLOAD_DIR"] = str(tmp_path / "uploads")
    os.environ["ARTIFACTS_DIR"] = str(tmp_path / "artifacts")
    os.environ["REPORTS_DIR"] = str(tmp_path / "reports")
    # import target module
    import app.services.automl_service as automl_mod
    from app.core.config import get_settings

    # Replace imported AutoML with our fake implementation.
    monkeypatch.setattr(automl_mod, "AutoML", FakeAutoML)

    # monkeypatch metrics used
    monkeypatch.setattr(automl_mod, "accuracy_score", lambda y_true, y_pred: 1.0)
    monkeypatch.setattr(automl_mod, "mean_squared_error", lambda a, b, squared: 0.0)

    # create a minimal CSV
    job_id = "testjob"
    csv_path = Path(os.environ["UPLOAD_DIR"]) / f"{job_id}.csv"
    csv_path.write_text("a,b,target\n1,2,0\n3,4,1\n5,6,0\n7,8,1\n", encoding="utf-8")

    settings = get_settings()
    metadata = {"job_id": job_id, "target_column": "target", "task_type": "classification", "time_budget_seconds": 5}

    results = automl_mod.run_full_automl(settings, job_id, metadata)
    assert results["job_id"] == job_id
    assert "best_model_name" in results

    artifacts_dir = Path(os.environ["ARTIFACTS_DIR"]) / job_id
    assert (artifacts_dir / "leaderboard.csv").exists()
    assert (artifacts_dir / "best_model.pkl").exists()
    assert (artifacts_dir / "results.json").exists()
    # deployment package
    assert (artifacts_dir / "deployment" / "predict.py").exists()
