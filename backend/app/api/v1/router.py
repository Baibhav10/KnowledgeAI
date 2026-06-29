"""
The v1 router aggregates all route modules under /api/v1.
As we add auth, documents, and chat, we just import and include
their routers here — main.py never changes.
"""
from fastapi import APIRouter
from app.api.v1.routes import health

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["Health"])