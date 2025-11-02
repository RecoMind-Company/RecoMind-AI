# RecoMind AI Analyst Microservice - Deployment Guide

## 1\. Project Overview

This document outlines the deployment and operational procedures for the **RecoMind AI Analyst Microservice**.

This service is a containerized, asynchronous application designed to perform long-running, complex data analysis tasks. It exposes a simple REST API for clients to submit analysis jobs and poll for results, while the heavy processing (AI agents, data analysis, report generation) is handled in the background.

**Core Technologies:**

  * **API:** FastAPI (running on Uvicorn)
  * **Task Queue:** Celery
  * **Broker & Result Backend:** Redis
  * **AI Pipeline:** CrewAI / LangGraph
  * **Database Connector:** `pyodbc` (for MS SQL Server)
  * **Containerization:** Docker & Docker Compose

## 2\. Service Architecture

The system runs as a multi-container application orchestrated by `docker-compose`. The architecture consists of three core services:

1.  **`recomind-api` (The "Front Door"):**

      * A lightweight FastAPI server.
      * **Responsibility:** Receives client requests (`POST /run_analysis`), validates them, submits the job to the Redis queue, and immediately returns a `task_id`. It also provides an endpoint (`GET /get_status`) for clients to poll for results.
      * Does **not** perform any heavy computation.

2.  **`recomind-worker` (The "Engine"):**

      * A Celery worker process.
      * **Responsibility:** Listens to the Redis queue for new tasks. When a task appears, it executes the entire `run_full_pipeline` (CrewAI, database queries, LangGraph analysis).
      * This is where all the long-running (10+ min) processing occurs. It updates the task status in Redis as it progresses.

3.  **`recomind-redis` (The "Mailbox"):**

      * A standard Redis container.
      * **Responsibility:** Acts as the central message broker for Celery (passing tasks from the `api` to the `worker`) and as the result backend (storing the final report or error message).

## 3\. Deployment Instructions

This service is deployed using a pre-built Docker image from Docker Hub and a `docker-compose.yml` file for orchestration.

### Prerequisites

  * A host machine with Docker and Docker Compose installed.
  * Network access to the production Vector Database (Supabase).
  * All required environment variables (see below) stored securely (e.g., in AWS Secrets Manager, HashiCorp Vault, or a secured `.env` file).

### Step 1: Prepare the `docker-compose.yml`

The developer will provide the official Docker Image name (e.g., `your-username/recomind-api:1.0`). You must update the `docker-compose.yml` file to use this pre-built image instead of building from source.

```yaml
# docker-compose.yml

services:
  
  redis:
    image: redis:7-alpine
    container_name: recomind-redis
    hostname: recomind-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  api:
    # --- IMPORTANT ---
    # Change 'build: .' to 'image: ...'
    image: [your-dockerhub-username]/recomind-api:latest # <-- Use the pre-built image
    # ---
    
    container_name: recomind-api
    env_file:
      - .env
    environment:
      # This "tricks" crewai into using OpenRouter
      - OPENAI_API_KEY=${OPENROUTER_API_KEY}
      - OPENAI_API_BASE=${BASE_URL}
      - OPENAI_MODEL_NAME=${crewai_LLM_MODEL}
    ports:
      - "8000:8000"
    depends_on:
      - redis

  worker:
    # --- IMPORTANT ---
    # Change 'build: .' to 'image: ...'
    image: [your-dockerhub-username]/recomind-api:latest # <-- Use the *exact same* image
    # ---
    
    container_name: recomind-worker
    command: celery -A celery_worker.celery_app worker --loglevel=info -P gevent
    env_file:
      - .env
    environment:
      # The worker also needs all the secrets
      - OPENAI_API_KEY=${OPENROUTER_API_KEY}
      - OPENAI_API_BASE=${BASE_URL}
      - OPENAI_MODEL_NAME=${crewai_LLM_MODEL}
    depends_on:
      - redis
      - api 

volumes:
  redis_data:
```

### Step 2: Create the `.env` File

On the production host, create a `.env` file in the same directory as `docker-compose.yml`. This file must contain all production secrets and configurations.

```ini
# .envexample - Production Configuration

# Celery Configuration (MUST point to the service name from docker-compose)
CELERY_BROKER_URL=redis://............

# LLM Provider Configuration (OpenRouter)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
crewai_LLM_MODEL=openrouter/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
langgraph_LLM_MODEL=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
BASE_URL=https://openrouter.ai/api/v1

# Vector DB Credentials (Supabase)
VECTOR_DB_HOST=aws-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
VECTOR_DB_USER=.
VECTOR_DB_PASSWORD=xxxxxxxxxxxxxxxxxx
VECTOR_DB_NAME=xxxxxxxxxxxxxxx
```

### Step 3: Launch the Application

Once the `docker-compose.yml` and `.env` files are in place, run the following command to pull the images and start all services in detached mode.

```bash
docker-compose up -d
```

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

1.  **Submit Job:** `POST /run_analysis` with `company_id` and `user_request`.

      * **Immediate Response:** `(200 OK)`
        ```json
        {
          "task_id": "a5b4c3d2-1234-5678-...",
          "status": "PENDING",
          "message": "Analysis task has been submitted."
        }
        ```

2.  **Poll for Status:** `GET /get_status/{task_id}` (e.g., every 15-30 seconds).

      * **While Running:** `(200 OK)`
        ```json
        {
          "task_id": "a5b4c3d2-...",
          "status": "PROGRESS",
          "result": "STAGE 2: Fetching Data..."
        }
        ```
      * **On Success:** `(200 OK)`
        ```json
        {
          "task_id": "a5b4c3d2-...",
          "status": "SUCCESS",
          "result": "# Final Report\n\n## Analysis...\n..."
        }
        ```
      * **On Failure:** `(200 OK)`
        ```json
        {
          "task_id": "a5b4c3d2-...",
          "status": "FAILURE",
          "result": "Error: Database query failed. Connection timed out."
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
