# Automated-Machine-Learning-AutoML-Platform-with-MLflow-and-Celery

## FastAPI Starter

The `api/` folder now contains a production-ready FastAPI starter with:

- `GET /health` health check
- CORS enabled from environment variables
- modular `routes/`, `services/`, and `schemas/` packages
- logging configuration
- Docker support

The project scaffold also includes a separate `worker/` service for Celery jobs, a root `docker-compose.yml` for Redis, MLflow, API, and worker, and a shared `.env.example` for local configuration.

## Run Locally

```bash
cd api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Set values in `api/.env.example` or copy them into a local `.env` file before running.

## Run With Compose

```bash
docker compose up --build
```

## Run ports

- API: configured by `API_PORT` (default 8000). Set in root `.env.example`.

To build and run (detached):

```bash
docker compose up --build -d
```
