"""
Health check routes
"""

from datetime import datetime

from fastapi import APIRouter

from ..schemas.pydantic_models import HealthResponse

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/live")
async def liveness():
    """Liveness probe"""
    return {"status": "alive"}


@router.get("/ready")
async def readiness():
    """Readiness probe"""
    return {"status": "ready"}
