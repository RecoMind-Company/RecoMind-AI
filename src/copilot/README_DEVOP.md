# RecoMind Copilot - DevOps Guide

## Overview
This service provides the NL-to-SQL Copilot API with background task processing using Celery and Redis.

## Architecture
- **API**: FastAPI on port 8002 (`/copilot` prefix)
- **Worker**: Celery worker processing `copilot_queue`
- **Broker**: Redis for task queue and result backend

## Environment Variables

Create a `.env` file in this directory with:

```env
# === API Settings ===
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8002

# === Celery/Redis ===
CELERY_BROKER_URL=redis://copilot-redis:6379/0

# === LLM Configuration (OpenRouter) ===
OPENROUTER_API_KEY=your_openrouter_api_key
BASE_URL=https://openrouter.ai/api/v1
crewai_LLM_MODEL=openai/gpt-4o

# === Metadata Database (PostgreSQL) ===
METADATA_DB_HOST=your_host
METADATA_DB_PORT=5432
METADATA_DB_NAME=recomind_metadata
METADATA_DB_USER=your_user
METADATA_DB_PASSWORD=your_password

# === Vector Database ===
VECTOR_DB_HOST=your_vector_db_host
VECTOR_DB_NAME=your_vector_db
VECTOR_DB_USER=your_user
VECTOR_DB_PASSWORD=your_password
```

## Running with Docker

### Build and Start All Services
```bash
docker-compose up --build
```

### Start in Background
```bash
docker-compose up -d --build
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
```

### Stop Services
```bash
docker-compose down
```

### Rebuild After Code Changes
```bash
docker-compose up --build
```

## API Endpoints

### Base URL
`http://localhost:8002/copilot`

### Sync Endpoints (Original)
- `GET /health` - Health check
- `POST /chat` - Synchronous chat (blocks until complete)

### Async Endpoints (New - Recommended)
- `POST /chat/async` - Submit chat task to queue (returns immediately)
- `GET /chat/status/{task_id}` - Poll for task status/result

### Example Usage

#### Submit Async Chat Request
```bash
curl -X POST "http://localhost:8002/copilot/chat/async" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": "fb140d33-7e96-474d-a06d-ab3a6c65d1a9",
    "team_name": "Sales",
    "user_question": "What is the total revenue in 2024?"
  }'
```

Response:
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PENDING",
  "message": "Chat task has been submitted to the queue."
}
```

#### Check Task Status
```bash
curl "http://localhost:8002/copilot/chat/status/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

Response (In Progress):
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "PROGRESS",
  "result": "STAGE 2: Initializing AI agents..."
}
```

Response (Complete):
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "SUCCESS",
  "result": {
    "success": true,
    "answer": "The total revenue in 2024 was $1,234,567.",
    "error": null
  }
}
```

## Port Configuration
- **Copilot API**: 8002
- **Copilot Redis**: 6380 (external) / 6379 (internal)
- **Reporting API**: 8001
- **Reporting Redis**: 6379

## Troubleshooting

### Check if Redis is Running
```bash
docker-compose ps
```

### Check Worker Logs
```bash
docker-compose logs -f worker
```

### Restart Worker Only
```bash
docker-compose restart worker
```

### Clear Redis Queue
```bash
docker-compose exec redis redis-cli FLUSHALL
```
