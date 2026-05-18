from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe. Returns runtime info; never accesses external services."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": "0.0.1",
        "env": settings.env,
    }
