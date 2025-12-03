# main.py
"""
RecoMind NL-to-SQL Copilot API
FastAPI application entry point.
"""

import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Create FastAPI app
app = FastAPI(
    title="RecoMind NL-to-SQL Copilot",
    description="Natural Language to SQL query generation with CrewAI agents",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None,
)

# Configure CORS based on environment
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

logger.info(f"Starting RecoMind Copilot API in {ENVIRONMENT} mode")


# Development server
if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
    )
