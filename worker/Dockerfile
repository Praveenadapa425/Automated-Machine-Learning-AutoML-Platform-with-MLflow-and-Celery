FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app ./app

USER app

HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD celery -A app.celery_app:celery_app inspect ping --timeout=5 || exit 1

CMD ["celery", "-A", "app.celery_app:celery_app", "worker", "--loglevel=info", "--concurrency=1", "--hostname=automl@%h"]