from .base_cms_client import BaseCMSClient
from shared_models.models import NotionCredentials

class NotionClient(BaseCMSClient):
    def __init__(self, credentials: NotionCredentials):
        super().__init__(credentials)
        self.base_url = "https://api.notion.com/v1"

    async def publish_article(self, article_data: dict, **kwargs):
        endpoint = "/pages"
        return await self._make_request("post", endpoint, json=article_data)
