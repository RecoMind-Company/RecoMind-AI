"""
Planning Board - AI Backend
============================
Convert strategic plans into organized executable tasks
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.routes import router as api_router, mock_router
from core.config import settings


def _allowed_origins() -> list[str]:
    return [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode")
    logger.info(f"API available at http://{settings.API_HOST}:{settings.API_PORT}{settings.API_PREFIX}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""

    app = FastAPI(
        title=settings.APP_NAME,
        description="AI Backend for Planning Board",
        version="1.0.0",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        root_path=settings.ROOT_PATH,
        servers=[{"url": settings.ROOT_PATH}],
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_router, prefix=settings.API_PREFIX)
    app.include_router(mock_router, prefix=settings.API_PREFIX)

    return app


app = create_app()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
