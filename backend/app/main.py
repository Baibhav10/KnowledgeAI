from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import router as v1_router

limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    app = FastAPI(
    title="KnowledgeAI",
    description="""
    A Retrieval-Augmented Generation (RAG) API that lets users upload documents 
    and chat with their content using a local AI model.

    ## Features
    - JWT authentication with multi-tenant organization model
    - Document upload and async processing pipeline
    - Vector similarity search via pgvector
    - Streaming RAG chat with source citations
    - Persistent conversation history per document
    """,
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Rate limit exceeded handler
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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