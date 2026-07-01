"""
Company Client
==============
Retrieves company information from the .NET API.
"""

import asyncio
from typing import Any, Dict

import httpx
from loguru import logger

from core.config import settings
from core.exceptions import CompanyServiceException
from clients.auth_client import auth_client
from models.entities import CompanyInfo


class CompanyClient:
    """API client for retrieving company information."""

    async def get_company(self, company_id: str) -> CompanyInfo:
        """
        Retrieve company information by company ID.
        Extracts only business-related fields: name, industry, size, description, country.
        """
        url = f"{settings.DOTNET_API_BASE_URL}/{settings.DOTNET_COMPANY_ENDPOINT.format(company_id=company_id)}"

        for attempt in range(settings.LLM_MAX_RETRIES):
            try:
                headers = await auth_client.get_auth_headers()
                async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    return self._parse_company(data)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.warning("Unauthorized - refreshing auth token")
                    await auth_client._login()
                    continue
                if attempt == settings.LLM_MAX_RETRIES - 1:
                    raise CompanyServiceException(
                        message=f"Company API returned status {e.response.status_code}",
                        details={"company_id": company_id, "url": url},
                    )
            except httpx.RequestError as e:
                if attempt == settings.LLM_MAX_RETRIES - 1:
                    raise CompanyServiceException(
                        message=f"Company API request failed: {str(e)}",
                        details={"company_id": company_id, "url": url},
                    )

            await asyncio.sleep(2 ** attempt)

    @staticmethod
    def _parse_company(data: Dict[str, Any]) -> CompanyInfo:
        """Extract only business-related fields from the API response."""
        return CompanyInfo(
            name=data.get("name", ""),
            industry=data.get("industry", ""),
            size=data.get("size", ""),
            description=data.get("description", ""),
            country=data.get("country", ""),
        )


# Singleton instance
company_client = CompanyClient()
