"""
Health check endpoint.
Every production service needs one — load balancers, Docker,
and Kubernetes all ping /health to know if the app is alive.
"""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("")
async def health_check() -> dict:
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }