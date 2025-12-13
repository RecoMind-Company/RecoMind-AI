"""
FastAPI application entry point
"""
import logging
from fastapi import FastAPI
from dotenv import load_dotenv

from app.routes import pipeline_routes

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RecoMind Data Embedding Pipeline",
    description="API to trigger data ingestion and team assignment pipeline via task queue.",
    version="3.0.0",
    root_path="/embedding"
)

# Include routers
app.include_router(pipeline_routes.router, tags=["Pipeline"])


@app.on_event("startup")
async def startup_event():
    logger.info("RecoMind Data Embedding API starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("RecoMind Data Embedding API shutting down...")
