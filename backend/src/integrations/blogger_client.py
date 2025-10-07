from .base_cms_client import BaseCMSClient
from shared_models.models import BloggerCredentials

class BloggerClient(BaseCMSClient):
    def __init__(self, credentials: BloggerCredentials):
        super().__init__(credentials)
        self.base_url = "https://www.googleapis.com/blogger/v3"

    async def publish_article(self, article_data: dict, **kwargs):
        blog_id = getattr(self.credentials, "blog_id", None)
        endpoint = f"/blogs/{blog_id}/posts"
        payload = {
            "title": article_data.get("title", ""),
            "content": article_data.get("content", ""),
            "labels": article_data.get("tags", []),
        }
        return await self._make_request("post", endpoint, json=payload)
