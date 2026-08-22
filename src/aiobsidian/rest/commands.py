from __future__ import annotations

from pydantic import BaseModel

from ..models.commands import Command
from ._base import BaseResource


class _CommandListing(BaseModel):
    """The envelope the commands endpoint wraps its one list in.

    Private on purpose: callers get the list itself, so the wrapper
    only has to survive as far as `list()` reading `.commands` off it.

    Attributes:
        commands: The commands the vault answers to.
    """

    commands: list[Command]


class CommandsResource(BaseResource):
    """List and execute Obsidian commands."""

    __slots__ = ()

    _BASE_URL = "/commands"

    async def list(self) -> list[Command]:
        """List all available Obsidian commands.

        Returns:
            A list of `Command` objects with `id` and `name` fields.

        Raises:
            APIParseError: If the body is not the commands envelope.
        """
        response = await self._client.request("GET", f"{self._BASE_URL}/")
        return self._parse_as(response, _CommandListing).commands

    async def execute(self, command_id: str) -> None:
        """Execute an Obsidian command by its ID.

        Args:
            command_id: The unique identifier of the command
                (e.g. `"editor:toggle-bold"`).
        """
        await self._client.request("POST", f"{self._BASE_URL}/{command_id}/")
