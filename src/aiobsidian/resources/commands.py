from .._base_resource import BaseResource
from ..models.commands import Command


class CommandsResource(BaseResource):
    async def list(self) -> list[Command]:
        response = await self._client.request("GET", "/commands/")
        data = response.json()
        return [Command.model_validate(c) for c in data["commands"]]

    async def execute(self, command_id: str) -> None:
        await self._client.request("POST", f"/commands/{command_id}/")
