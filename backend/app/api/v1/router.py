from fastapi import APIRouter
from app.api.v1.routes import health, auth

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])