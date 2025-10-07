from backend.src.integrations.base_cms_client import BaseCMSClient
from shared_models.models import MediumCredentials

class MediumClient(BaseCMSClient):
    def __init__(self, credentials: MediumCredentials):
        super().__init__(credentials)
        self.headers.update({"Authorization": f"Bearer {credentials.access_token}"})

    async def _get_user_id(self) -> str:
        endpoint = "/me"
        response = await self._make_request("get", endpoint)
        return response["data"]["id"]

    async def publish_article(self, article_data: dict, **kwargs):
        user_id = kwargs.get("user_id") or await self._get_user_id()
        endpoint = f"/users/{user_id}/posts"
        if self.credentials.publication_id:
            article_data["publicationId"] = self.credentials.publication_id
        return await self._make_request("post", endpoint, json=article_data)
