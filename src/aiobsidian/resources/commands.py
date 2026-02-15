from .._base_resource import BaseResource
from ..models.commands import Command


class CommandsResource(BaseResource):
    """List and execute Obsidian commands."""

    _BASE_URL = "/commands"

    async def list(self) -> list[Command]:
        """List all available Obsidian commands.

        Returns:
            A list of `Command` objects with `id` and `name` fields.
        """
        response = await self._client.request("GET", f"{self._BASE_URL}/")
        data = response.json()
        return [Command.model_validate(c) for c in data["commands"]]

    async def execute(self, command_id: str) -> None:
        """Execute an Obsidian command by its ID.

        Args:
            command_id: The unique identifier of the command
                (e.g. `"editor:toggle-bold"`).
        """
        await self._client.request("POST", f"{self._BASE_URL}/{command_id}/")
