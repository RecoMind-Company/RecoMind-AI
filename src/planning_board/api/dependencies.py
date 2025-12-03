"""
API Dependencies
================
Middleware و Dependencies للـ API
"""

from typing import Optional
from fastapi import Header, HTTPException, Depends
from fastapi.security import APIKeyHeader
from loguru import logger

from core.config import settings


# API Key Header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    authorization: Optional[str] = Header(None)
) -> str:
    """
    التحقق من الـ API Key
    يقبل إما X-API-Key header أو Authorization: Bearer token
    """
    
    # في Development mode، نتخطى التحقق
    if settings.is_development and settings.DEBUG:
        logger.debug("🔓 Skipping API key verification in development mode")
        return "dev-mode"
    
    # Check X-API-Key header first
    if api_key:
        if api_key == settings.SERVICE_API_KEY:
            return api_key
        else:
            logger.warning("❌ Invalid API key provided")
            raise HTTPException(
                status_code=401,
                detail={"error": "Unauthorized", "message": "Invalid API key"}
            )
    
    # Check Authorization header
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            if token == settings.SERVICE_API_KEY:
                return token
    
    logger.warning("❌ No API key provided")
    raise HTTPException(
        status_code=401,
        detail={"error": "Unauthorized", "message": "API key required"}
    )


async def get_current_company(
    company_id: Optional[str] = Header(None, alias="X-Company-ID")
) -> Optional[str]:
    """
    استخراج Company ID من الـ Header (اختياري)
    """
    return company_id
