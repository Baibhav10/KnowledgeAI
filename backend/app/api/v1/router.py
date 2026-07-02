from fastapi import APIRouter
from app.api.v1.routes import health, auth, documents, search

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(search.router, prefix="/search", tags=["Search"])