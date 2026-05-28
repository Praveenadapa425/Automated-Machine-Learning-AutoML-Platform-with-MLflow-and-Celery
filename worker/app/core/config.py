import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AutoML Worker")
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
    mlflow_tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    upload_dir: str = os.getenv("UPLOAD_DIR", "/data/uploads")
    artifacts_dir: str = os.getenv("ARTIFACTS_DIR", "/data/artifacts")
    reports_dir: str = os.getenv("REPORTS_DIR", "/data/reports")
    allowed_extensions: str = os.getenv("ALLOWED_EXTENSIONS", ".csv")

    @property
    def allowed_extension_list(self) -> List[str]:
        return [item.strip() for item in self.allowed_extensions.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()