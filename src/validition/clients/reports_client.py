"""
Reports Client
==============
Retrieves reports from the .NET API for the Resource Analysis agent.
"""

import asyncio
from typing import Any, Dict, List

import httpx
from loguru import logger

from core.config import settings
from core.exceptions import ReportsServiceException
from clients.auth_client import auth_client


class ReportsClient:
    """API client for retrieving team reports."""

    async def get_reports(self, team_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve reports for a team.
        limit defaults to settings.REPORT_LIMIT.
        """
        if limit is None:
            limit = settings.REPORT_LIMIT
        url = f"{settings.DOTNET_API_BASE_URL}/{settings.DOTNET_REPORTS_ENDPOINT.format(team_id=team_id, limit=limit)}"

        for attempt in range(settings.LLM_MAX_RETRIES):
            try:
                headers = await auth_client.get_auth_headers()
                async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    data = response.json()
                    return self._parse_reports(data)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.warning("Unauthorized - refreshing auth token")
                    await auth_client._login()
                    continue
                if attempt == settings.LLM_MAX_RETRIES - 1:
                    raise ReportsServiceException(
                        message=f"Reports API returned status {e.response.status_code}",
                        details={"team_id": team_id, "url": url},
                    )
            except httpx.RequestError as e:
                if attempt == settings.LLM_MAX_RETRIES - 1:
                    raise ReportsServiceException(
                        message=f"Reports API request failed: {str(e)}",
                        details={"team_id": team_id, "url": url},
                    )

            await asyncio.sleep(2 ** attempt)

    @staticmethod
    def _parse_reports(data: Any) -> List[Dict[str, Any]]:
        """Normalize various response shapes into a list of report dicts."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("items", "data", "result", "reports", "Reports"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return []


# Singleton instance
reports_client = ReportsClient()
