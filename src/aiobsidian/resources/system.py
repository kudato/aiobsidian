from .._base_resource import BaseResource
from ..models.system import ServerStatus


class SystemResource(BaseResource):
    async def status(self) -> ServerStatus:
        response = await self._client.request("GET", "/")
        return ServerStatus.model_validate(response.json())

    async def openapi(self) -> str:
        response = await self._client.request("GET", "/openapi.yaml")
        return response.text
