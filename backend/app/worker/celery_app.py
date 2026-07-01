"""
Celery application factory.
BROKER_URL tells Celery where to send tasks (Redis).
RESULT_BACKEND tells Celery where to store task results (also Redis).
We keep Celery config here so it's separate from FastAPI's config.
"""
from celery import Celery

celery_app = Celery(
    "knowledge_base_ai",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)