from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIThemesResource(BaseCLIResource):
    """CLI resource for theme management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def current(self) -> dict[str, Any]:
        """Get the current theme information.

        Returns:
            Current theme details.
        """
        output = await self._cli._execute("theme")
        result: dict[str, Any] = json.loads(output)
        return result

    async def set(self, name: str) -> None:
        """Change the active theme.

        Args:
            name: Theme name to activate.
        """
        await self._cli._execute("theme:set", params={"name": name})

    async def install(self, name: str) -> None:
        """Install a theme from the community registry.

        Args:
            name: Theme name to install.
        """
        await self._cli._execute("theme:install", params={"name": name})

    async def uninstall(self, name: str) -> None:
        """Uninstall a theme.

        Args:
            name: Theme name to uninstall.
        """
        await self._cli._execute("theme:uninstall", params={"name": name})

    async def list(self) -> list[dict[str, Any]]:
        """List all installed themes.

        Returns:
            List of theme objects.
        """
        output = await self._cli._execute("themes")
        result: list[dict[str, Any]] = json.loads(output)
        return result
