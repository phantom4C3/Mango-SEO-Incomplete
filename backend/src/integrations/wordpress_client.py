from .base_cms_client import BaseCMSClient
from shared_models.models import WordPressCredentials

class WordPressClient(BaseCMSClient):
    def __init__(self, credentials: WordPressCredentials):
        super().__init__(credentials)
        self.base_url = f"{credentials.url.rstrip('/')}/wp-json/wp/v2"

    async def publish_article(self, article_data: dict, **kwargs):
        endpoint = "/posts"
        return await self._make_request("post", endpoint, json=article_data)
