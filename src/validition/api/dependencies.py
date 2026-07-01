"""
API Dependencies
================
Middleware and Dependencies for the API
"""

from typing import Optional
from fastapi import Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from core.config import settings


security = HTTPBearer(auto_error=False)


async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> str:
    """
    Verify the API Key.
    Accepts either Authorization: Bearer <token> or X-API-Key header.
    """

    # In Development mode, skip verification
    if settings.is_development and settings.DEBUG:
        logger.debug("Skipping API key verification in development mode")
        return "dev-mode"

    # Check X-API-Key header first
    if x_api_key:
        if x_api_key == settings.SERVICE_API_KEY:
            return x_api_key
        else:
            logger.warning("Invalid API key provided")
            raise HTTPException(
                status_code=401,
                detail={"error": "Unauthorized", "message": "Invalid API key"},
            )

    # Check Authorization: Bearer header
    if credentials:
        token = credentials.credentials
        if token == settings.SERVICE_API_KEY:
            return token
        else:
            logger.warning("Invalid API key provided")
            raise HTTPException(
                status_code=401,
                detail={"error": "Unauthorized", "message": "Invalid API key"},
            )

    logger.warning("No API key provided")
    raise HTTPException(
        status_code=401,
        detail={"error": "Unauthorized", "message": "API key required"},
    )
