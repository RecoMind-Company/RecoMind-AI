"""
Celery Application
==================
Celery configuration for async validation tasks
"""

from celery import Celery
from core.config import settings

# Create Celery app
celery_app = Celery(
    "validation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["workers.tasks"],
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
    result_expires=3600,

    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,

    # Task routing
    task_routes={
        "run_validation_task": {"queue": settings.CELERY_QUEUE_NAME},
        "health_check_task": {"queue": settings.CELERY_QUEUE_NAME},
    },

    # Task time limits (10 min hard, 8 min soft for large LLM pipelines)
    task_time_limit=600,
    task_soft_time_limit=480,
)


if __name__ == "__main__":
    celery_app.start()
