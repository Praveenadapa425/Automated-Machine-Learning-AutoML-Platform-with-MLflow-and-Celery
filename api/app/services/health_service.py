from datetime import UTC, datetime

from app.core.config import Settings
from app.schemas.health import HealthResponse


def build_health_response(settings: Settings) -> HealthResponse:
    return HealthResponse(
        service=settings.app_name,
        environment=settings.environment,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
    )
