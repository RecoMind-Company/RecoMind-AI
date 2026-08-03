"""RecoMind AI Analyst FastAPI Application Entry Point."""

import logging
import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(
    title="RecoMind AI Analyst API (with Celery)",
    description="API to trigger the full data analysis pipeline via a task queue.",
    version="2.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None,
    root_path="/reporting",
    servers=[{"url": "/reporting"}]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    logger.info("RecoMind AI Analyst API starting up...")

if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8001"))
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
