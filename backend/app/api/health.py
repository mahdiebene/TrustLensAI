"""Health check endpoint."""

from fastapi import APIRouter
from redis import asyncio as aioredis

from app.config import get_settings
from app.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check service health and connectivity."""
    settings = get_settings()
    services: dict[str, str] = {}

    # Check Redis
    try:
        redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis.ping()
        services["redis"] = "connected"
        await redis.aclose()
    except Exception:
        services["redis"] = "disconnected"

    # Check PostgreSQL (basic — full check requires SQLAlchemy session)
    services["postgres"] = "configured"

    # Check Neo4j
    services["neo4j"] = "configured"

    # Overall status
    status = "ok" if services.get("redis") == "connected" else "degraded"

    return HealthResponse(
        status=status,
        version="0.1.0",
        services=services,
    )
