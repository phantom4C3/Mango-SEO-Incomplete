# backend/src/integrations/base_cms_client.py
"""
Base CMS API Client - Generic interface for all CMS platforms.
Provides async HTTP request handling and connection testing.
Platform-specific logic (publish, get user_id, etc.) should be implemented in platform helpers.
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional

from ..core.config import settings
from ..core.exceptions import handle_api_error
from shared_models.models import CMSCredentials

logger = logging.getLogger(__name__)


class CMSIntegrationError(Exception):
    """Custom exception for CMS integration errors."""
    def __init__(self, detail: str, operation: str, cms_type: str):
        self.detail = detail
        self.operation = operation
        self.cms_type = cms_type
        super().__init__(f"{cms_type} error during {operation}: {detail}")


class BaseCMSClient:
    """
    Generic CMS API client.
    Handles async requests, generic headers, and connection testing.
    """
    def __init__(self, credentials: CMSCredentials):
        self.credentials = credentials
        self.cms_type = credentials.cms_platform.value
        self.base_url = getattr(credentials, "base_url", "")
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = self._prepare_headers()

    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare generic headers. Platform-specific headers are handled in helpers."""
        return {
            "Content-Type": "application/json",
            "User-Agent": f"MangoSEO-CMS-Client/1.0 ({self.cms_type})"
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _make_request(self, method: str, endpoint: str, max_retries: int = 3, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request with retries and exponential backoff.
        """
        for attempt in range(max_retries):
            try:
                if not self.session:
                    self.session = aiohttp.ClientSession(headers=self.headers)

                url = f"{self.base_url.rstrip('/')}{endpoint}"
                async with self.session.request(method.upper(), url, **kwargs) as response:
                    response.raise_for_status()

                    if response.status == 204:
                        return {}

                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        return await response.json()
                    else:
                        return {"text": await response.text()}

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == max_retries - 1:
                    raise CMSIntegrationError(str(e), "api_request", self.cms_type)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                raise CMSIntegrationError(str(e), "api_request", self.cms_type)

    async def test_connection(self, test_endpoint: str = "/") -> bool:
        """
        Generic connection test. Platform-specific endpoints should be provided by helper.
        """
        try:
            await self._make_request("get", test_endpoint)
            return True
        except Exception as e:
            raise CMSIntegrationError(str(e), "test_connection", self.cms_type)

    async def publish_article(self, article_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Base publish method.
        Platform-specific clients (MediumClient, WordPressClient, etc.) should override this.
        Returns:
            Dict with keys: cms_id, url/permalink
        """
        raise NotImplementedError(
            f"Publish logic not implemented for {self.cms_type}. "
            "Use a platform-specific client helper."
        )

    @staticmethod
    async def create_cms_client(credentials: CMSCredentials) -> "BaseCMSClient":
        """
        Factory: instantiate correct CMS client, test connection.
        Uses lazy imports to avoid circular dependencies.
        """
        cms_type = credentials.cms_platform.value.lower()
        client_cls = None

        # Lazy imports to prevent circular import issues
        if cms_type == "bitsandbytes":
            from .bitsandbytes_client import BitsAndBytesClient
            client_cls = BitsAndBytesClient
        elif cms_type == "blogger":
            from .blogger_client import BloggerClient
            client_cls = BloggerClient
        elif cms_type == "custom_rest_api":
            from .custom_rest_api_client import CustomRestAPIClient
            client_cls = CustomRestAPIClient
        elif cms_type == "framer":
            from .framer_client import FramerClient
            client_cls = FramerClient
        elif cms_type == "ghost":
            from .ghost_client import GhostClient
            client_cls = GhostClient
        elif cms_type == "hubspot":
            from .hubspot_client import HubSpotClient
            client_cls = HubSpotClient
        elif cms_type == "medium":
            from .medium_client import MediumClient
            client_cls = MediumClient
        elif cms_type == "notion":
            from .notion_client import NotionClient
            client_cls = NotionClient
        elif cms_type == "shopify":
            from .shopify_client import ShopifyClient
            client_cls = ShopifyClient
        elif cms_type == "substack":
            from .substack_client import SubstackClient
            client_cls = SubstackClient
        elif cms_type == "webflow":
            from .webflow_client import WebflowClient
            client_cls = WebflowClient
        elif cms_type == "wix":
            from .wix_client import WixClient
            client_cls = WixClient
        elif cms_type == "wordpress":
            from .wordpress_client import WordPressClient
            client_cls = WordPressClient

        if not client_cls:
            raise ValueError(f"No CMS client implementation found for: {cms_type}")

        client = client_cls(credentials)
        try:
            await client.test_connection()
            return client
        except Exception as e:
            if getattr(client, "session", None):
                await client.session.close()
            raise e
