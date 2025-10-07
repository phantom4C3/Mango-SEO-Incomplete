from .base_cms_client import BaseCMSClient
from shared_models.models import SubstackCredentials

class SubstackClient(BaseCMSClient):
    def __init__(self, credentials: SubstackCredentials):
        super().__init__(credentials)
        self.base_url = "https://substack.com/api/v1"

    async def publish_article(self, article_data: dict, **kwargs):
        endpoint = "/posts"
        return await self._make_request("post", endpoint, json=article_data)
