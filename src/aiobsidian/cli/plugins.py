from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIPluginsResource(BaseCLIResource):
    """CLI resource for plugin management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def enabled(self) -> list[dict[str, Any]]:
        """List enabled plugins.

        Returns:
            List of enabled plugin objects.
        """
        output = await self._cli._execute("plugins:enabled")
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def enable(self, plugin_id: str) -> None:
        """Enable a plugin.

        Args:
            plugin_id: Plugin identifier.
        """
        await self._cli._execute("plugin:enable", params={"id": plugin_id})

    async def disable(self, plugin_id: str) -> None:
        """Disable a plugin.

        Args:
            plugin_id: Plugin identifier.
        """
        await self._cli._execute("plugin:disable", params={"id": plugin_id})

    async def install(self, plugin_id: str) -> None:
        """Install a community plugin.

        Args:
            plugin_id: Plugin identifier from the community registry.
        """
        await self._cli._execute("plugin:install", params={"id": plugin_id})

    async def uninstall(self, plugin_id: str) -> None:
        """Uninstall a plugin.

        Args:
            plugin_id: Plugin identifier.
        """
        await self._cli._execute("plugin:uninstall", params={"id": plugin_id})

    async def reload(self, plugin_id: str) -> None:
        """Reload a plugin (useful during development).

        Args:
            plugin_id: Plugin identifier.
        """
        await self._cli._execute("plugin:reload", params={"id": plugin_id})

    async def list(self) -> list[dict[str, Any]]:
        """List all installed plugins.

        Returns:
            List of plugin objects.
        """
        output = await self._cli._execute("plugins")
        result: list[dict[str, Any]] = json.loads(output)
        return result
