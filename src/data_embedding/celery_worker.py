from celery import Celery
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read the Redis URL from the environment
REDIS_URL = os.environ.get("CELERY_BROKER_URL")

# Create the Celery app instance
celery_app = Celery(
    "ingestion_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["pipeline"]  # <-- Tell Celery to find tasks in 'pipeline.py'
)

celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True
)

if __name__ == "__main__":
    celery_app.start()