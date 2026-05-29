from __future__ import annotations

import json
import traceback
from pathlib import Path
from typing import Any

import joblib
import shutil
import mlflow
import numpy as np
import pandas as pd
from flaml import AutoML
from matplotlib import pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error

from app.core.config import Settings
from app.services.artifact_service import build_job_directory, build_report_directory


def prepare_job_paths(settings: Settings, job_id: str) -> dict[str, Path]:
    return {
        "artifacts": build_job_directory(settings, job_id),
        "reports": build_report_directory(settings, job_id),
    }


def run_full_automl(settings: Settings, job_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
    """Run a FLAML AutoML job and write artifacts.

    Produces: leaderboard.csv, best_model.pkl, results.json, (optional) feature_importance.png, shap_summary.png
    """
    csv_path = Path(settings.upload_dir) / f"{job_id}.csv"
    paths = prepare_job_paths(settings, job_id)
    artifacts_dir: Path = Path(paths["artifacts"])
    reports_dir: Path = Path(paths["reports"])

    # Load data
    df = pd.read_csv(csv_path)
    target = metadata.get("target_column")
    task_type = metadata.get("task_type", "classification")
    time_budget = int(metadata.get("time_budget_seconds", 60))

    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in uploaded CSV")

    X = df.drop(columns=[target])
    y = df[target]

    # Split
    stratify = y if task_type == "classification" else None
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=stratify
        )
    except ValueError:
        # Small datasets may not support stratification; fall back to a plain split.
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Preprocessing
    numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = [c for c in X.columns if c not in numeric_cols]

    numeric_transformer = make_pipeline(SimpleImputer(strategy="mean"), StandardScaler())
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
    cat_transformer = make_pipeline(SimpleImputer(strategy="most_frequent"), encoder)

    preprocessor = ColumnTransformer(
        [("num", numeric_transformer, numeric_cols), ("cat", cat_transformer, categorical_cols)],
        remainder="drop",
        sparse_threshold=0,
    )

    # Fit preprocessor on training data
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc = preprocessor.transform(X_test)

    # Run FLAML AutoML
    automl = AutoML()
    metric = "accuracy" if task_type == "classification" else "rmse"
    try:
        mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.set_experiment(f"automl-job-{job_id}")
        with mlflow.start_run() as run:
            automl.fit(
                X_train_proc,
                y_train,
                task=task_type,
                time_budget=time_budget,
                metric=metric,
            )

            # Evaluate
            preds = automl.predict(X_test_proc)
            if task_type == "classification":
                score = float(accuracy_score(y_test, preds))
            else:
                score = float(mean_squared_error(y_test, preds, squared=False))

            best_model_name = getattr(automl, "best_estimator", None) or str(automl.model)
            mlflow.log_param("time_budget_seconds", time_budget)
            mlflow.log_param("task_type", task_type)
            mlflow.log_metric("score", score)

            # Save model artifact
            model_path = artifacts_dir / "best_model.pkl"
            try:
                joblib.dump(automl.model, model_path)
            except Exception:
                # fallback: save automl object
                joblib.dump(automl, model_path)

            # Create deployment package (model + lightweight inference script + requirements)
            try:
                deployment_dir = artifacts_dir / "deployment"
                deployment_dir.mkdir(parents=True, exist_ok=True)

                # copy the model into deployment folder
                try:
                    shutil.copy2(model_path, deployment_dir / "best_model.pkl")
                except Exception:
                    # fallback: write again
                    joblib.dump(automl.model, deployment_dir / "best_model.pkl")

                # inference script
                predict_py = deployment_dir / "predict.py"
                predict_py.write_text(
                    """import joblib
import pandas as pd

# Simple inference script. Usage: python predict.py /path/to/input.csv
model = joblib.load('best_model.pkl')

def predict(df: pd.DataFrame):
    # Assumes the uploaded CSV has the same feature columns used for training.
    preds = model.predict(df)
    return preds

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python predict.py /path/to/input.csv')
        sys.exit(2)
    df = pd.read_csv(sys.argv[1])
    out = predict(df)
    print(out.tolist())
""",
                    encoding="utf-8",
                )

                # minimal requirements for deployment
                (deployment_dir / "requirements.txt").write_text(
                    "joblib\npandas\nscikit-learn\n", encoding="utf-8"
                )

                # small README
                (deployment_dir / "README.md").write_text(
                    """Deployment package for job {job_id}

Includes `best_model.pkl`, a simple `predict.py` inference script, and `requirements.txt`.
Run: `python predict.py /path/to/features.csv`
""".format(job_id=job_id),
                    encoding="utf-8",
                )
            except Exception:
                # do not fail the job if deployment package creation fails
                pass

            # Leaderboard: create simple CSV with best model
            leaderboard_path = artifacts_dir / "leaderboard.csv"
            lb_df = pd.DataFrame([
                {"rank": 1, "model_name": best_model_name, "score": score}
            ])
            lb_df.to_csv(leaderboard_path, index=False)

            # Feature importance (best-effort)
            try:
                fi_path = reports_dir / "feature_importance.png"
                model_for_fi = getattr(automl, "model", None)
                importances = None
                if hasattr(model_for_fi, "feature_importances_"):
                    importances = model_for_fi.feature_importances_
                elif hasattr(model_for_fi, "coef_"):
                    importances = np.abs(model_for_fi.coef_).ravel()

                if importances is not None and len(importances) == X_train_proc.shape[1]:
                    plt.figure(figsize=(8, 6))
                    # Build feature names from preprocessor
                    try:
                        feature_names = []
                        if hasattr(preprocessor, "get_feature_names_out"):
                            feature_names = list(preprocessor.get_feature_names_out(X.columns))
                        else:
                            feature_names = [f"f{i}" for i in range(len(importances))]
                        idx = np.argsort(importances)[::-1][:20]
                        plt.barh([feature_names[i] for i in idx[::-1]], importances[idx[::-1]])
                        plt.tight_layout()
                        plt.savefig(fi_path)
                        plt.close()
                    except Exception:
                        plt.close()

            except Exception:
                # ignore feature importance errors
                pass

            # SHAP summary (best-effort)
            try:
                shap_path = reports_dir / "shap_summary.png"
                try:
                    explainer = None
                    import shap

                    explainer = shap.Explainer(automl.model)
                    shap_values = explainer(X_test_proc)
                    plt.figure(figsize=(8, 6))
                    shap.plots.bar(shap_values, show=False)
                    plt.savefig(shap_path)
                    plt.close()
                except Exception:
                    plt.close()
            except Exception:
                pass

            # Log artifacts to MLflow
            try:
                mlflow.log_artifact(str(model_path))
                mlflow.log_artifact(str(leaderboard_path))
                if fi_path.exists():
                    mlflow.log_artifact(str(fi_path))
                if shap_path.exists():
                    mlflow.log_artifact(str(shap_path))
            except Exception:
                pass

            run_id = run.info.run_id

    except Exception as exc:
        traceback.print_exc()
        raise

    # write results.json
    results = {
        "job_id": job_id,
        "best_model_name": str(best_model_name),
        "best_model_score": float(score),
        "evaluation_metric": metric,
        "mlflow_run_id": run_id,
        "start_time": None,
        "end_time": None,
    }

    results_file = artifacts_dir / "results.json"
    with results_file.open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)

    return results
