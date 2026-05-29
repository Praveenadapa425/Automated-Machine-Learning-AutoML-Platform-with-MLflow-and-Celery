# Automated Machine Learning Platform (AutoML)

A containerized AutoML platform built with FastAPI (API), Celery (asynchronous jobs), Redis (broker), and MLflow (experiment tracking). The worker runs FLAML-based AutoML searches and produces artifacts (leaderboard, model, SHAP/feature plots, and a small deployment package).

This repository is intended as a modular starter for experimentation and integration into ML pipelines.

**Highlights**
- FastAPI-based HTTP API for job submission and status queries.
- Celery worker for background AutoML jobs (FLAML) with MLflow logging.
- Docker Compose configuration for local orchestration (Redis, MLflow, API, worker).
- Artifacts persistence via Docker volumes and a small deployment packaging step.

**Contents**
- `api/`: FastAPI application and routes.
- `worker/`: Celery worker, FLAML integration, artifact generation.
- `docker-compose.yml`: Local development orchestration.
- `.env.example`: Environment variable template used by services.

**Quick Start (Docker Compose)**

Prerequisites: Docker and Docker Compose installed.

1. Build and start services:

```bash
docker compose up --build -d
```

2. Submit a job (replace file/fields as appropriate):

```bash
curl -X POST "http://localhost:8000/jobs" \
	-F "csv_file=@/path/to/dataset.csv" \
	-F "target_column=target" \
	-F "task_type=classification" \
	-F "time_budget_seconds=60"
```

3. Check status:

```bash
curl http://localhost:8000/jobs/<job_id>
```

4. Retrieve results when complete:

```bash
curl http://localhost:8000/jobs/<job_id>/results
```

**Running Locally (API)**

```bash
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Ensure you copy `.env.example` to `.env` or set the required environment variables before running locally.

**API Endpoints (summary)**
- `POST /jobs` — submit a CSV dataset and AutoML job (returns `202 Accepted` with `job_id`).
- `GET /jobs/{job_id}` — get job status (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`).
- `GET /jobs/{job_id}/results` — when job is successful returns JSON with keys: `job_id`, `best_model_name`, `best_model_score`, `evaluation_metric`, `mlflow_run_id`.
- `GET /health` — simple service health check.

**Artifacts & Persistence**
- Uploads, artifacts, and reports are stored under the shared data volume mounted at `/data` inside the API and worker containers. Each job creates `ARTIFACTS_DIR/{job_id}` and `REPORTS_DIR/{job_id}` with generated files including `results.json`, `leaderboard.csv`, `best_model.pkl`, and a `deployment/` package.

**Environment Variables (key)**
- `UPLOAD_DIR` — path for uploaded CSVs (default `/data/uploads`).
- `ARTIFACTS_DIR` — path where worker writes artifacts (default `/data/artifacts`).
- `REPORTS_DIR` — path for reports and plots (default `/data/reports`).
- `MLFLOW_TRACKING_URI` — MLflow server URL (e.g., `http://mlflow:5000`).
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` — Redis broker/backends.

See `./.env.example` for a full template of supported environment variables.

**Testing**

Unit and integration-style tests are available under `tests/`. Run them locally with:

```bash
pip install -r api/requirements.txt
pip install pytest
pytest -q
```

Tests mock heavy dependencies (FLAML, MLflow) so they run without large ML installs.

**CI**
A basic GitHub Actions workflow is included at `.github/workflows/ci.yml` to run tests on push and pull requests.

**Next steps / Ideas**
- Improve model packaging (add dockerized inference runtime, model signature).
- Add end-to-end integration tests using docker compose in CI.
- Add authentication for the API and RBAC for artifact downloads.

--
For detailed implementation see the `api/` and `worker/` directories.


## Run ports

- API: configured by `API_PORT` (default 8000). Set in root `.env.example`.

To build and run (detached):

```bash
docker compose up --build -d
```
