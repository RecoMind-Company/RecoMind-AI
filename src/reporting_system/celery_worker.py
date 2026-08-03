"""Celery worker application initialization."""

import logging
from celery import Celery
from config.settings import CELERY_BROKER_URL, CELERY_QUEUE_NAME

logger = logging.getLogger(__name__)

celery_app = Celery(
    "recomind_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL,
    include=["pipeline"],
)

celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    task_default_queue=CELERY_QUEUE_NAME,
)

if __name__ == "__main__":
    celery_app.start()
