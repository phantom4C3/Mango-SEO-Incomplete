from .base_cms_client import BaseCMSClient
from shared_models.models import WixCredentials

class WixClient(BaseCMSClient):
    def __init__(self, credentials: WixCredentials):
        super().__init__(credentials)
        self.base_url = "https://www.wixapis.com"

    async def publish_article(self, article_data: dict, **kwargs):
        endpoint = "/blog/v3/posts"
        return await self._make_request("post", endpoint, json=article_data)
