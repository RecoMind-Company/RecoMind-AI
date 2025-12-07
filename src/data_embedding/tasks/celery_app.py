"""
Celery application configuration
"""
import os
from celery import Celery
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Read Redis URL from environment
REDIS_URL = os.environ.get("CELERY_BROKER_URL")

# Create Celery app instance
celery_app = Celery(
    "recomind_ingestion_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["tasks.pipeline_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

if __name__ == "__main__":
    celery_app.start()
