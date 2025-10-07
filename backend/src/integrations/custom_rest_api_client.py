from .base_cms_client import BaseCMSClient
from shared_models.models import CustomRestAPICredentials

class CustomRestAPIClient(BaseCMSClient):
    def __init__(self, credentials: CustomRestAPICredentials):
        super().__init__(credentials)
        self.base_url = credentials.base_url.rstrip("/")

    async def publish_article(self, article_data: dict, **kwargs):
        endpoint = getattr(self.credentials, "endpoint", "/posts")
        return await self._make_request("post", endpoint, json=article_data)
