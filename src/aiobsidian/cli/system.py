from __future__ import annotations

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
        output = await self._cli._execute("version")
        return output.strip()

    async def help(self) -> str:
        """Get the CLI help text listing all available commands.

        Returns:
            Help text as printed by the CLI, including usage notes and the
            parameters of every command.
        """
        output = await self._cli._execute("help")
        return output.strip()

    async def reload(self) -> None:
        """Reload the Obsidian window."""
        await self._cli._execute("reload")

    async def restart(self) -> None:
        """Restart the Obsidian application."""
        await self._cli._execute("restart")

    async def vaults(self) -> list[str]:
        """List all known vaults (desktop only).

        Returns:
            List of vault names.
        """
        output = await self._cli._execute("vaults")
        return self._parse_lines(output)
