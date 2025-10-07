# ai-worker/app/services/serpapi.py
from __future__ import annotations
from typing import Dict, Any, Optional, List
import httpx
import logging

from ..core.config import settings  # where your SERPAPI_KEY should live

logger = logging.getLogger(__name__)

# Shared HTTP client (singleton)
_http_client: Optional[httpx.AsyncClient] = None
_BASE_URL = "https://serpapi.com/search.json"


class SerpApiClient:
    """Async client for interacting with SerpAPI."""

    def __init__(self, api_key: str):
        global _http_client
        if _http_client is None:
            _http_client = httpx.AsyncClient(timeout=30.0)
        self._client = _http_client
        self.api_key = api_key

    async def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform GET request to SerpAPI with authentication."""
        params = {**params, "api_key": self.api_key}

        try:
            response = await self._client.get(_BASE_URL, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"SerpAPI HTTP error: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected SerpAPI error: {str(e)}")
            raise

    async def search(
        self, query: str, location: Optional[str] = None, gl: str = "us", hl: str = "en"
    ) -> Dict[str, Any]:
        """Perform a SERP search."""
        params = {"q": query, "location": location, "gl": gl, "hl": hl}
        return await self._request(params)

    async def get_related_keywords(self, keyword: str) -> Dict[str, Any]:
        """Get related keyword suggestions via SerpAPI."""
        params = {"q": keyword, "type": "related_keywords"}
        return await self._request(params)

    async def close(self):
        """Close shared HTTP client."""
        await self._client.aclose()


# ✅ Module-level singleton (like supabase_client)
serpapi_client: SerpApiClient = SerpApiClient(api_key=settings.serpapi_key)


# from serpapi import GoogleSearch

# class SerpApiClient:
#     """Async client for interacting with SerpAPI."""

#     def __init__(self):
#         self._client = GoogleSearch()
#         self.api_key = settings.serpapi_key  # Ensure this matches your .env variable

#     async def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
#         """Perform GET request to SerpAPI with authentication."""
#         params["api_key"] = self.api_key  # Add API key to params if not set in environment
#         try:
#             response = await self._client.get_json(params)
#             return response
#         except Exception as e:
#             logger.error(f"Unexpected SerpAPI error: {str(e)}")
#             raise
