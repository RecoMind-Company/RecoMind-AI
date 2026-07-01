"""
Authentication Client
=====================
Handles login, token caching, refresh, and retry for the .NET API.
"""

import asyncio
import time
from typing import Any, Dict, Optional

import httpx
from loguru import logger

from core.config import settings
from core.exceptions import AuthenticationException


class AuthenticationClient:
    """
    Dedicated authentication service for the .NET API.
    Handles login, bearer token caching, token refresh, and retry on failure.
    """

    def __init__(self):
        self._token: Optional[str] = None
        self._token_obtained_at: Optional[float] = None
        self._lock = asyncio.Lock()

    def _is_token_valid(self) -> bool:
        if not self._token or not self._token_obtained_at:
            return False
        elapsed = time.time() - self._token_obtained_at
        return elapsed < settings.AUTH_TOKEN_CACHE_TTL

    async def get_token(self) -> str:
        """Return a valid bearer token, logging in or refreshing as needed."""
        if self._is_token_valid():
            return self._token

        async with self._lock:
            if self._is_token_valid():
                return self._token
            await self._login()
            return self._token

    async def get_auth_headers(self) -> Dict[str, str]:
        """Return HTTP headers with the bearer token injected."""
        token = await self.get_token()
        return {"Authorization": f"Bearer {token}"}

    async def _login(self) -> None:
        """Authenticate with the .NET API and cache the token."""
        login_url = f"{settings.DOTNET_API_BASE_URL}/{settings.DOTNET_AUTH_ENDPOINT}"
        payload = {
            "email": settings.AUTH_EMAIL,
            "password": settings.AUTH_PASSWORD,
        }

        for attempt in range(settings.LLM_MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                    response = await client.post(login_url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    token = self._extract_token(data)
                    if not token:
                        raise AuthenticationException(
                            message="Login response did not contain a token",
                            details={"response_keys": list(data.keys()) if isinstance(data, dict) else str(type(data))},
                        )
                    self._token = token
                    self._token_obtained_at = time.time()
                    logger.info("Successfully authenticated with .NET API")
                    return
            except httpx.HTTPStatusError as e:
                logger.warning(f"Login HTTP error (attempt {attempt + 1}): {e.response.status_code}")
                if attempt == settings.LLM_MAX_RETRIES - 1:
                    raise AuthenticationException(
                        message=f"Authentication failed with status {e.response.status_code}",
                        details={"url": login_url},
                    )
            except httpx.RequestError as e:
                logger.warning(f"Login request error (attempt {attempt + 1}): {e}")
                if attempt == settings.LLM_MAX_RETRIES - 1:
                    raise AuthenticationException(
                        message=f"Authentication request failed: {str(e)}",
                        details={"url": login_url},
                    )

            await asyncio.sleep(2 ** attempt)

    @staticmethod
    def _extract_token(data: Any) -> Optional[str]:
        """Extract token from various possible response shapes."""
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            for key in ("token", "accessToken", "access_token", "Token", "AccessToken"):
                if key in data:
                    return data[key]
            for value in data.values():
                if isinstance(value, str) and len(value) > 20:
                    return value
        return None


# Singleton instance
auth_client = AuthenticationClient()
