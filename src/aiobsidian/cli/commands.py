from __future__ import annotations

from ._base import BaseCLIResource


class CLICommandsResource(BaseCLIResource):
    """CLI resource for Obsidian command operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def execute(self, command_id: str) -> None:
        """Execute an Obsidian command by its ID.

        Args:
            command_id: Obsidian command identifier
                (e.g. ``"editor:toggle-bold"``).
        """
        await self._cli._execute("command", params={"id": command_id})

    async def list(self, *, filter: str | None = None) -> list[str]:
        """List available Obsidian commands.

        Args:
            filter: Filter commands by ID prefix.

        Returns:
            List of command IDs (e.g. `"editor:toggle-bold"`).
        """
        params = {"filter": filter} if filter else None
        output = await self._cli._execute("commands", params=params)
        return self._parse_lines(output)
