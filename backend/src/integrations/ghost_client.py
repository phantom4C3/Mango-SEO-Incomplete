from .base_cms_client import BaseCMSClient
from shared_models.models import GhostCredentials

class GhostClient(BaseCMSClient):
    def __init__(self, credentials: GhostCredentials):
        super().__init__(credentials)
        self.base_url = f"{credentials.url.rstrip('/')}/ghost/api/v3/content"

    async def publish_article(self, article_data: dict, **kwargs):
        endpoint = "/posts"
        return await self._make_request("post", endpoint, json={"posts": [article_data]})
