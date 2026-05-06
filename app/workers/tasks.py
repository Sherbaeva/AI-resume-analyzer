"""Celery tasks (async bridge for CPU-bound or long-running ops)."""
import asyncio
from app.workers.celery_app import celery_app
import structlog

logger = structlog.get_logger()


@celery_app.task(name="tasks.ping")
def ping() -> str:
    """Simple health task to verify worker connectivity."""
    return "pong"
