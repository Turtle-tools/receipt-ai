"""
Background tasks using Celery.
"""

from celery import Celery
from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "receipt_ai",
    broker=settings.redis_url or "redis://localhost:6379/0",
    backend=settings.redis_url or "redis://localhost:6379/0",
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minute warning
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
