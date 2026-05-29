FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENV API_PORT=8000

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# curl used by healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY --chown=app:app app ./app
COPY --chown=app:app .env.example ./.env.example

USER app

EXPOSE ${API_PORT}

HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD curl -f http://localhost:${API_PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT}"]
