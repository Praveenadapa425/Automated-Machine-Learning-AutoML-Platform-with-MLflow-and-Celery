import os
from dataclasses import dataclass
from functools import lru_cache
from typing import List


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "FastAPI Starter")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000")
    api_prefix: str = os.getenv("API_PREFIX", "")
    upload_dir: str = os.getenv("UPLOAD_DIR", "/data/uploads")

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
