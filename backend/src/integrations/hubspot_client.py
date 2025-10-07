from .base_cms_client import BaseCMSClient
from shared_models.models import HubSpotCredentials

class HubSpotClient(BaseCMSClient):
    def __init__(self, credentials: HubSpotCredentials):
        super().__init__(credentials)
        self.base_url = "https://api.hubapi.com"

    async def publish_article(self, article_data: dict, **kwargs):
        endpoint = "/content/api/v2/blog-posts"
        return await self._make_request("post", endpoint, json=article_data)
