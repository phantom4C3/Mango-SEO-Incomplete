from .base_cms_client import BaseCMSClient
from shared_models.models import FramerCredentials

class FramerClient(BaseCMSClient):
    def __init__(self, credentials: FramerCredentials):
        super().__init__(credentials)
        self.base_url = "https://api.framer.com/v1"

    async def publish_article(self, article_data: dict, **kwargs):
        endpoint = "/pages"
        return await self._make_request("post", endpoint, json=article_data)
