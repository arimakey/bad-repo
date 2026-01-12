from fastapi import APIRouter
from src.core.config import settings

router = APIRouter(prefix="", tags=["health"])


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "project": settings.PROJECT_NAME}
