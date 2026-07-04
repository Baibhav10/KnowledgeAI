from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import router as v1_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Knowledge Base AI",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router, prefix=settings.API_V1_PREFIX)

    @app.on_event("startup")
    async def on_startup():
        logger.info(
            "Knowledge Base AI started | env=%s version=%s",
            settings.APP_ENV,
            settings.APP_VERSION,
        )

    return app


app = create_app()