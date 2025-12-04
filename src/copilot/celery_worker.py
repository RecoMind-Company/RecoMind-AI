# celery_worker.py
"""
Celery application configuration for RecoMind Copilot.
Handles background task processing with Redis as broker.
"""

import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables from .env file
# This MUST be at the top, before accessing os.environ
load_dotenv()

# Get Redis URL from environment
REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Create Celery app instance
celery_app = Celery(
    "copilot_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["pipeline"]  # Tell Celery to look for tasks in 'pipeline.py'
)

# Celery configuration
celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    task_default_queue='copilot_queue',  # Isolate this worker's queue
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

if __name__ == "__main__":
    celery_app.start()
