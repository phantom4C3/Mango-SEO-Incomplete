# ai-worker/app/tools/google_search_tool.py

from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import logging
import httpx

from ..clients.api_clients import serpapi_client  # relative import
from ..core.config import settings  # lowercase settings

logger = logging.getLogger(__name__)


class GoogleSearchTool:
    """
    High-level Google search utility.
    Wraps SerpAPI and optionally Google Custom Search.
    Provides parsing, snippet extraction, competitor analysis, ranking checks.
    """

    def __init__(self):
        # Optional fallback to Google Custom Search API
        self.gcs_key = getattr(settings, "google_custom_search_api_key", None)
        self.gcs_cx = getattr(settings, "serpapi_search_engine_id", None)

    async def search(
        self, query: str, num_results: int = 5, time_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform a search using SerpAPI (primary) or Google Custom Search (fallback).
        """
        try:
            if settings.serpapi_key:
                return await self._search_serpapi(query, num_results, time_range)
            elif self.gcs_key and self.gcs_cx:
                return await self._search_google_custom_search(query, num_results)
            else:
                raise Exception("No search API configured")
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            return []

    async def _search_serpapi(
        self, query: str, num_results: int, time_range: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Search using SerpAPI with optional time filtering."""
        try:
            data = await serpapi_client.search(query=query)

            # Limit results
            data = {
                **data,
                "organic_results": data.get("organic_results", [])[:num_results],
            }

            return self._parse_serpapi_results(data)
        except Exception as e:
            logger.error(f"SerpAPI search failed: {str(e)}")
            return []

    async def _search_google_custom_search(
        self, query: str, num_results: int
    ) -> List[Dict[str, Any]]:
        """Fallback to Google Custom Search API."""
        params = {
            "key": self.gcs_key,
            "cx": self.gcs_cx,
            "q": query,
            "num": min(num_results, 10),
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1", params=params
                )
                response.raise_for_status()
                data = response.json()
            return self._parse_gcs_results(data)
        except Exception as e:
            logger.error(f"Google Custom Search failed: {str(e)}")
            return []

    def _parse_serpapi_results(self, data: Dict) -> List[Dict[str, Any]]:
        results = []
        for r in data.get("organic_results", []):
            results.append(
                {
                    "title": r.get("title"),
                    "link": r.get("link"),
                    "snippet": r.get("snippet"),
                    "position": r.get("position"),
                    "domain": urlparse(r.get("link", "")).netloc if r.get("link") else "",
                    "rich_snippet": r.get("rich_snippet"),
                }
            )
        return results

    def _parse_gcs_results(self, data: Dict) -> List[Dict[str, Any]]:
        return [
            {
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet"),
                "domain": urlparse(item.get("link", "")).netloc if item.get("link") else "",
            }
            for item in data.get("items", [])
        ]

    # ---------------- High-level utilities ---------------- #

    async def extract_snippets(self, query: str, num_results: int = 5) -> List[str]:
        results = await self.search(query, num_results)
        return [r.get("snippet", "") for r in results if r.get("snippet")]

    async def search_news(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        return await self.search(f"{query} news", num_results, time_range="d")

    async def find_competitors(self, product_name: str, num_results: int = 10) -> List[Dict[str, Any]]:
        results = await self.search(f"{product_name} alternatives OR competitors OR similar", num_results)
        competitors = []
        for result in results:
            snippet = result.get("snippet", "").lower()
            if any(term in snippet for term in ["alternative", "competitor", "similar", "compare"]):
                competitors.append({
                    "name": result["title"].split("|")[0].split("-")[0].strip(),
                    "url": result["link"],
                    "description": result["snippet"],
                })
        return competitors

    async def extract_people_also_ask(self, query: str) -> List[Dict[str, Any]]:
        """Extract 'People Also Ask' questions using SerpAPI."""
        try:
            data = await serpapi_client.search(query=query)
            return [
                {
                    "question": q.get("question"),
                    "answer": q.get("answer"),
                    "source": q.get("source", {}).get("link"),
                }
                for q in data.get("related_questions", [])
            ]
        except Exception as e:
            logger.warning(f"Failed to extract 'People Also Ask': {str(e)}")
            return []

    async def check_ranking(self, website_url: str, keyword: str) -> Optional[int]:
        results = await self.search(keyword, num_results=50)
        for position, result in enumerate(results, 1):
            if website_url in result.get("link", ""):
                return position
        return None

    async def get_site_links(self, domain: str, num_results: int = 20) -> List[Dict[str, Any]]:
        results = await self.search(f"site:{domain}", num_results)
        return [
            {"url": r["link"], "title": r["title"], "snippet": r["snippet"]}
            for r in results
        ]


# ---------------- Singleton instance ---------------- #
google_search_tool = GoogleSearchTool()
