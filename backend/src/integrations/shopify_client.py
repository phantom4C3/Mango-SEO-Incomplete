from .base_cms_client import BaseCMSClient
from shared_models.models import ShopifyCredentials

class ShopifyClient(BaseCMSClient):
    def __init__(self, credentials: ShopifyCredentials):
        super().__init__(credentials)
        self.base_url = f"https://{credentials.shop_name}.myshopify.com/admin/api/2023-10"

    async def publish_article(self, article_data: dict, **kwargs):
        blog_id = getattr(self.credentials, "blog_id", None)
        endpoint = f"/blogs/{blog_id}/articles.json"
        payload = {"article": article_data}
        return await self._make_request("post", endpoint, json=payload)
