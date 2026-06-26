"""
Celery Application
==================
Celery configuration for Async Tasks
"""

from celery import Celery
from core.config import settings

# Create Celery app
celery_app = Celery(
    "planning_board",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["workers.tasks"]
)

# Celery Configuration
celery_app.conf.update(
    task_default_queue=settings.CELERY_QUEUE_NAME,
    task_track_started=True,
    broker_connection_retry_on_startup=True,

    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result settings
    result_expires=3600,  # 1 hour

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,

    # Task routing
    task_routes={
        "generate_plan_task": {"queue": settings.CELERY_QUEUE_NAME},
        "health_check_task": {"queue": settings.CELERY_QUEUE_NAME},
    },

    # Task time limits
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
)


if __name__ == "__main__":
    celery_app.start()
