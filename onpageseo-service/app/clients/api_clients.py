# import osonpageseo-service\app\clients\api_clients.py
import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import aiohttp 

# Modern Google auth imports
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ✅ Use shared settings
from ..core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings() 



class GoogleSearchConsoleClient:
    def __init__(self, service_account_info: Dict[str, Any] = None, site_url: str = None):
        """
        Initialize with service account info (dict, not file path)
        """
        self.site_url = site_url or ""
        
        if not service_account_info:
            raise ValueError("Service account info is required")
            
        try:
            # Create credentials from dict, not file
            self.credentials = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
            )
        except Exception as e:
            logger.error(f"Failed to create GSC credentials: {e}")
            raise

    async def get_metrics(self, url: str, days: int = 30) -> Dict[str, Any]:
        """Get GSC performance metrics asynchronously"""
        try:
            # Refresh credentials if needed
            if not self.credentials.valid:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.credentials.refresh, Request())

            # Build service in thread to avoid blocking
            loop = asyncio.get_event_loop()
            service = await loop.run_in_executor(
                None, 
                lambda: build("searchconsole", "v1", credentials=self.credentials)
            )

            request_body = {
                "startDate": (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d"),
                "endDate": datetime.utcnow().strftime("%Y-%m-%d"),
                "dimensions": ["date"],
                "dimensionFilterGroups": [{
                    "filters": [{
                        "dimension": "page",
                        "operator": "equals",
                        "expression": url
                    }]
                }]
            }

            # Execute query in thread
            response = await loop.run_in_executor(
                None,
                lambda: service.searchanalytics().query(
                    siteUrl=self.site_url, 
                    body=request_body
                ).execute()
            )
            
            rows = response.get("rows", [])
            if not rows:
                return {"clicks": 0, "impressions": 0, "ctr": 0, "position": 0}

            return {
                "clicks": sum(r.get("clicks", 0) for r in rows),
                "impressions": sum(r.get("impressions", 0) for r in rows),
                "ctr": sum(r.get("ctr", 0) for r in rows) / len(rows),
                "position": sum(r.get("position", 0) for r in rows) / len(rows)
            }
            
        except HttpError as e:
            logger.error(f"GSC API error: {e}")
            return {}
        except Exception as e:
            logger.error(f"GSC unexpected error: {e}")
            return {}

class PageSpeedClient:
    """Google PageSpeed Insights API using API key only"""

    BASE_URL = "https://pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed"

    def __init__(self):
        # No service account required
        self.api_key = settings.pagespeed_api_key
        if not self.api_key:
            raise ValueError("PAGEPEED_API_KEY must be set in environment")

    async def get_metrics(self, url: str, strategy: str = "mobile") -> Dict[str, Any]:
        """Get PageSpeed metrics using only API key"""
        try:
            params = {
                "url": url,
                "strategy": strategy,
                "category": ["performance", "accessibility", "seo", "best-practices"],
                "key": self.api_key  # <-- API key only
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"PageSpeed API failed ({resp.status}): {error_text}")
                        return {}

                    data = await resp.json()
                    return self._parse_metrics(data, strategy)

        except Exception as e:
            logger.error(f"PageSpeed API error: {e}")
            return {}


    # Keep the same _parse_metrics method
    @staticmethod
    def _parse_metrics(data: Dict, strategy: str) -> Dict[str, Any]:
        # ... (unchanged from your original code)
        """Parse PageSpeed API response"""
        lighthouse = data.get("lighthouseResult", {})
        audits = lighthouse.get("audits", {})
        categories = lighthouse.get("categories", {})
        
        # Core Web Vitals (LCP, FID, CLS, INP)
        loading_experience = data.get("loadingExperience", {})
        metrics = loading_experience.get("metrics", {})
        
        return {
            "strategy": strategy,
            "fetch_time": datetime.utcnow().isoformat(),
            "scores": {
                "performance": categories.get("performance", {}).get("score", 0) * 100,
                "accessibility": categories.get("accessibility", {}).get("score", 0) * 100,
                "seo": categories.get("seo", {}).get("score", 0) * 100,
                "best_practices": categories.get("best-practices", {}).get("score", 0) * 100,
            },
            "core_web_vitals": {
                "lcp": audits.get("largest-contentful-paint", {}).get("numericValue", 0),
                "fid": audits.get("max-potential-fid", {}).get("numericValue", 0),
                "cls": audits.get("cumulative-layout-shift", {}).get("numericValue", 0),
                "inp": audits.get("interaction-to-next-paint", {}).get("numericValue", 0),
            },
            "field_data": {
                "lcp": metrics.get("LARGEST_CONTENTFUL_PAINT_MS", {}).get("percentile", 0),
                "fid": metrics.get("FIRST_INPUT_DELAY_MS", {}).get("percentile", 0),
                "cls": metrics.get("CUMULATIVE_LAYOUT_SHIFT_SCORE", {}).get("percentile", 0),
            }
        }

class GA4Client:
    """
    Google Analytics Data API (GA4) client
    Docs: https://developers.google.com/analytics/devguides/reporting/data/v1
    """

    BASE_URL = "https://analyticsdata.googleapis.com/v1beta"

    def __init__(self, service_account_info: Dict[str, Any], property_id: str = None):
        """
        Initialize with service account info (dict)
        """
        self.property_id = property_id or settings.ga4_property_id
        self.credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"]
        )

    async def _get_access_token(self) -> str:
        """Get valid OAuth2 token"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.credentials.refresh, Request())
        return self.credentials.token

    async def get_traffic_data(self, url_path: str, days: int = 30) -> Dict[str, Any]:
        """Fetch GA4 traffic data for a specific URL path"""
        try:
            access_token = await self._get_access_token()
            
            endpoint = f"{self.BASE_URL}/properties/{self.property_id}:runReport"
            payload = {
                "dateRanges": [{
                    "startDate": f"{days}daysAgo",
                    "endDate": "today"
                }],
                "dimensions": [{"name": "pagePath"}],
                "metrics": [
                    {"name": "sessions"},
                    {"name": "totalUsers"},
                    {"name": "screenPageViews"}
                ],
                "dimensionFilter": {
                    "filter": {
                        "fieldName": "pagePath",
                        "stringFilter": {
                            "matchType": "CONTAINS",
                            "value": url_path
                        }
                    }
                }
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint, 
                    headers=headers, 
                    json=payload, 
                    timeout=30
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"GA4 API failed ({resp.status}): {error_text}")
                        return {}

                    data = await resp.json()
                    return self._parse_ga4_response(data)

        except Exception as e:
            logger.error(f"GA4 API error: {e}")
            return {}

    @staticmethod
    def _parse_ga4_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse GA4 report response"""
        rows = data.get("rows", [])
        if not rows:
            return {"sessions": 0, "users": 0, "pageviews": 0}

        metrics = rows[0].get("metricValues", [])
        return {
            "sessions": int(metrics[0]["value"]) if len(metrics) > 0 else 0,
            "users": int(metrics[1]["value"]) if len(metrics) > 1 else 0,
            "pageviews": int(metrics[2]["value"]) if len(metrics) > 2 else 0,
        }
        
        
        
        
class SerpAPIClient:
    """SerpAPI client for competitor analysis and keyword research"""
    
    BASE_URL = "https://serpapi.com/search"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.serpapi_key
        if not self.api_key:
            logger.warning("SerpAPI key not configured - competitor analysis will be limited")
    
    async def get_keyword_ranks(self, query: str, domain: str = None) -> Dict[str, Any]:
        """Get search results for a keyword"""
        if not self.api_key:
            return None
            
        params = {
            "q": query,
            "api_key": self.api_key,
            "engine": "google",
            "num": 20  # Get top 20 results
        }
        
        if domain:
            params["q"] = f"site:{domain} {query}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        logger.error(f"SerpAPI failed ({resp.status}) for query: {query}")
                        return None
                    return await resp.json()
        except Exception as e:
            logger.error(f"SerpAPI error for query {query}: {e}")
            return None
    
    async def get_domain_analysis(self, domain: str) -> Dict[str, Any]:
        """Get basic domain analysis"""
        if not self.api_key:
            return None
            
        # Get indexed pages count
        site_search = await self.get_keyword_ranks("", domain)
        indexed_pages = 0
        if site_search and "search_information" in site_search:
            indexed_pages = site_search["search_information"].get("total_results", 0)
        
        return {
            "indexed_pages": indexed_pages,
            "domain": domain
        }       
 
   
   
   
# --- helper functions and client initialization ---
def get_google_service_account_info():
    """Parse and fix the Google Service Account JSON from settings"""
    if not settings.google_service_account_json:
        logger.error("Google Service Account JSON not configured")
        return None

    try:
        # Parse JSON from .env if it's a string
        if isinstance(settings.google_service_account_json, str):
            sa_info = json.loads(settings.google_service_account_json)
        else:
            sa_info = settings.google_service_account_json.copy()
            
        # Fix the private key by replacing literal \n with actual newlines
        if 'private_key' in sa_info and isinstance(sa_info['private_key'], str):
            sa_info['private_key'] = sa_info['private_key'].replace('\\n', '\n')
            
        return sa_info
    except Exception as e:
        logger.error(f"Failed to parse Google Service Account JSON: {e}")
        return None

# Get the parsed service account info
google_service_account_info = get_google_service_account_info()

# Create API clients with service account
api_clients = {}
if google_service_account_info:
    api_clients = {
        "gsc": GoogleSearchConsoleClient(service_account_info=google_service_account_info),
        "pagespeed": PageSpeedClient(),  # ✅ FIXED
        "ga4": GA4Client(service_account_info=google_service_account_info),
        "serp": SerpAPIClient()  # This stays with API key
    }
else:
    logger.warning("Google API clients not initialized due to missing service account config")
    api_clients = {
        "serp": SerpAPIClient()  # SERP API can work without Google services
    }