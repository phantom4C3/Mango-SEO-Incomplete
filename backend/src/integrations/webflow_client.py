from .base_cms_client import BaseCMSClient
from shared_models.models import WebflowCredentials

class WebflowClient(BaseCMSClient):
    def __init__(self, credentials: WebflowCredentials):
        super().__init__(credentials)
        self.base_url = "https://api.webflow.com"

    async def publish_article(self, article_data: dict, **kwargs):
        collection_id = kwargs.get("collection_id") or getattr(self.credentials, "collection_id", None)
        endpoint = f"/collections/{collection_id}/items"
        return await self._make_request("post", endpoint, json={"fields": article_data})
