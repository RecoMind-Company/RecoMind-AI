# Data Ingestion Microservice - Deployment Guide

## 1\. Project Overview

This document outlines the deployment and operational procedures for the **Data Ingestion Microservice**.

This service is a containerized, asynchronous application designed to perform long-running data ingestion and embedding tasks (approx. 3-4 minutes). It exposes a simple REST API for clients to submit ingestion jobs and poll for results, while the heavy processing is handled in the background.

**Core Technologies:**

  * **API:** FastAPI (running on Uvicorn)
  * **Task Queue:** Celery
  * **Broker & Result Backend:** Redis
  * **Data Pipeline:** Custom Python scripts (Pandas, `pyodbc`, SentenceTransformers)
  * **Containerization:** Docker & Docker Compose

## 2\. Service Architecture

The system runs as a multi-container application orchestrated by `docker-compose`. The architecture consists of three core services:

1.  **`recomind-ingestion-api` (The "Front Door"):**

      * A lightweight FastAPI server.
      * **Responsibility:** Receives client requests (`POST /start-pipeline`), submits the job to the Redis queue, and immediately returns a `task_id`. It also provides an endpoint (`GET /get_status`) for clients to poll for results.

2.  **`recomind-ingestion-worker` (The "Engine"):**

      * A Celery worker process.
      * **Responsibility:** Listens to the Redis queue for new tasks. When a task appears, it executes the entire `run_ingestion_pipeline_task` (fetching credentials, connecting to DB, generating embeddings, etc.). This is where the 3-4 minute processing occurs.

3.  **`recomind-ingestion-redis` (The "Mailbox"):**

      * A standard Redis container.
      * **Responsibility:** Acts as the central message broker (passing tasks from `api` to `worker`) and as the result backend (storing the final success/failure status).

-----

## 3\. Deployment Instructions

This service is deployed using a pre-built Docker image from Docker Hub and a `docker-compose.yml` file for orchestration.

### Step 1: Prepare the `docker-compose.yml`

The `docker-compose.yml` file provided by the developer defines the services. It must be updated to point to the correct Docker Hub image.

```yaml
# docker-compose.yml

services:
  
  redis:
    image: redis:7-alpine
    container_name: recomind-ingestion-redis
    hostname: recomind-ingestion-redis
    ports:
      - "6379:6379"

  api:
    # --- IMPORTANT ---
    # Change 'build: .' to 'image: ...'
    image: hossamtaha9/recomind-ai-vector:latest # <-- Use the pre-built image
    # ---
    
    container_name: recomind-ingestion-api
    env_file:
      - .env  # Load all secrets
    ports:
      - "8000:8000"
    depends_on:
      - redis
    dns:
      - 8.8.8.8 # Public DNS for external requests

  worker:
    # --- IMPORTANT ---
    # Use the *exact same* pre-built image
    image: hossamtaha9/recomind-ai-vector:latest # <-- Use the pre-built image
    # ---
    
    container_name: recomind-ingestion-worker
    command: celery -A celery_worker.celery_app worker --loglevel=info -P gevent
    env_file:
      - .env  # The worker also needs all the secrets
    depends_on:
      - redis
    dns:
      - 8.8.8.8 # Public DNS for external requests
```

### Step 2: Create the `.env` File

On the production host, create a `.env` file in the same directory as `docker-compose.yml`. This file must contain all production secrets and configurations required by the pipeline.

```ini
# .env - Production Configuration

# 1. Celery Configuration
# This MUST point to the Redis service name defined in docker-compose
CELERY_BROKER_URL=redis://recomind-ingestion-redis:6379/0

# 2. External API Credentials
# Secrets needed by the pipeline to fetch database credentials
API_LOGIN_URL=https://apirecomind.azurewebsites.net/api/Authenticate/Login
API_USERNAME=example_user
API_PASSWORD=example_password
COMPANY_ID=fb140d33-7e96-474d-a06d-ab3a6c65d1a9
# ... (Add any other secrets the pipeline needs) ...
```

### Step 3: Launch the Application

Once the `docker-compose.yml` and `.env` files are in place, run the following command to pull the images and start all services in detached mode.

```bash
# Pull the latest version of the image
docker pull hossamtaha9/recomind-ai-vector:latest

# Start all services
docker-compose up -d
```

-----

## 4\. Monitoring & Verification

### Health Check

The API provides a health check endpoint for load balancers and automated monitoring systems.

  * **Endpoint:** `GET /health`
  * **Success Response (200 OK):**
    ```json
    {"status": "ok"}
    ```

### API Usage (Client-Side Flow)

The client (.NET Backend) will follow this asynchronous flow:

1.  **Submit Job:** `POST /start-pipeline`

      * **Immediate Response:** `(200 OK)`
        ```json
        {
          "task_id": "a5b4c3d2-1234-5678-...",
          "status": "PENDING",
          "message": "Ingestion task has been submitted."
        }
        ```

2.  **Poll for Status:** `GET /get_status/{task_id}` (e.g., every 15-30 seconds).

      * **While Running:** `(200 OK)`
        ```json
        {
          "task_id": "a5b4c3d2-...",
          "status": "PROGRESS",
          "result": "Pipeline Started..."
        }
        ```
      * **On Success:** `(200 OK)`
        ```json
        {
          "task_id": "a5b4c3d2-...",
          "status": "SUCCESS",
          "result": {
            "status": "success",
            "message": "Pipeline completed successfully."
          }
        }
        ```
      * **On Failure:** `(200 OK)`
        ```json
        {
          "task_id": "a5b4c3d2-...",
          "status": "FAILURE",
          "result": "Error: Read timed out. (read timeout=20)"
        }
        ```

### Viewing Logs

To view the real-time logs from all services (API, Worker, and Redis):

```bash
docker-compose logs -f
```

To view logs for a specific service (e.g., the worker):

```bash
docker-compose logs -f worker
```

### Stopping the Application

To stop all running services:

```bash
docker-compose down
```