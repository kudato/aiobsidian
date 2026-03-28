from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLISystemResource(BaseCLIResource):
    """CLI resource for general system commands.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def version(self) -> str:
        """Get the Obsidian version.

        Returns:
            Obsidian version string.
        """
        return await self._cli._execute("version")

    async def help(self) -> list[dict[str, Any]]:
        """List all available CLI commands.

        Returns:
            List of command descriptions.
        """
        output = await self._cli._execute("help")
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def reload(self) -> None:
        """Reload the Obsidian window."""
        await self._cli._execute("reload")

    async def restart(self) -> None:
        """Restart the Obsidian application."""
        await self._cli._execute("restart")

    async def vaults(self) -> list[dict[str, Any]]:
        """List all known vaults (desktop only).

        Returns:
            List of vault objects.
        """
        output = await self._cli._execute("vaults")
        result: list[dict[str, Any]] = json.loads(output)
        return result
