# --- [MODIFIED FILE] ---
# This file defines the Celery application.
# It now loads environment variables from a .env file.

from celery import Celery
import os                  # <-- [MODIFICATION] Import os
from dotenv import load_dotenv # <-- [MODIFICATION] Import load_dotenv

# --- [MODIFICATION] ---
# Load environment variables from .env file (if it exists)
# This MUST be at the top, before accessing os.environ
load_dotenv()
# --- [MODIFICATION END] ---


# --- [MODIFICATION] ---
# Now, we read the URL from the environment variable "CELERY_BROKER_URL".
REDIS_URL = os.environ.get("CELERY_BROKER_URL")
# --- [MODIFICATION END] ---


# Create the Celery app instance
celery_app = Celery(
    "recomind_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["pipeline"]  # <-- IMPORTANT: Tell Celery to look for tasks in 'pipeline.py'
)

celery_app.conf.update(
    task_track_started=True,
    broker_connection_retry_on_startup=True
)

if __name__ == "__main__":
    # This allows you to run the worker directly
    celery_app.start()

